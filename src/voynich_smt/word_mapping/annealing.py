"""Discrete dictionary annealing with deterministic checkpoints and archives."""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import tempfile

from voynich_smt.data.corpus import digest
from .incremental import IncrementalScorer
from .mapping import WordMapping
from .mutations import MutationCatalog, injective_changes


@dataclass(frozen=True)
class SearchConfig:
    seed: int = 42
    restarts: int = 4
    steps_per_restart: int = 10000
    active_types: int = 100
    initial_temperature: float = 5.0
    final_temperature: float = 0.05
    collapse_weight: float = 0.0
    archive_size: int = 100
    archive_min_distance: int = 1
    mutation_weights: tuple[float, ...] = (0.5, 0.2, 0.2, 0.1)
    initialization: str = 'mixed'
    frequency_weight: float = 0.0
    injective: bool = False

    def __post_init__(self):
        for name in ('restarts', 'steps_per_restart', 'active_types', 'archive_size', 'archive_min_distance'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f'{name} must be positive')
        if self.initialization not in {'mixed', 'frequency', 'random', 'lemma-aware'}:
            raise ValueError('Unknown initialization')
        if not all(math.isfinite(v) and v > 0 for v in (self.initial_temperature, self.final_temperature)):
            raise ValueError('Temperatures must be finite and positive')
        if not math.isfinite(self.collapse_weight) or self.collapse_weight < 0:
            raise ValueError('Invalid collapse weight')
        if not math.isfinite(self.frequency_weight) or self.frequency_weight < 0:
            raise ValueError('Invalid frequency weight')
        if type(self.injective) is not bool:
            raise ValueError('injective must be Boolean')
        if (len(self.mutation_weights) != 4 or
                not all(math.isfinite(v) and v >= 0 for v in self.mutation_weights) or
                self.mutation_weights[0] <= 0):
            raise ValueError('Four operator weights required; replacement must have positive support')


def _tuples(value):
    return tuple(_tuples(v) for v in value) if isinstance(value, list) else value


class Annealer:
    def __init__(self, model, candidates, segments, config=SearchConfig(), *, input_sha256=None):
        if model.training_sha256 != candidates.training_sha256:
            raise ValueError('Candidate/model training identities differ')
        self.model, self.candidates, self.config = model, candidates, config
        self.segments = tuple(tuple(s) for s in segments)
        self.rng = random.Random(config.seed)
        self.restart = 0
        self.step = 0
        self.evaluations = 0
        self.archive = []
        self.statistics = {kind: {'proposed': 0, 'accepted': 0, 'improved': 0}
                           for kind in ('replace', 'swap', 'inflection', 'lemma')}
        paths = [Path(__file__), Path(__file__).with_name('incremental.py'),
                 Path(__file__).with_name('mutations.py'), Path(__file__).with_name('ngram.py'),
                 Path(__file__).with_name('candidates.py'), Path(__file__).with_name('mapping.py'),
                 Path(__file__).with_name('objective.py')]
        self.protocol = {'version': 1, 'config': asdict(config), 'model_sha256': model.identity,
            'candidates_sha256': digest(asdict(candidates)), 'ciphertext_sha256': digest(self.segments),
            'public_input_sha256': input_sha256,
            'python': platform.python_version(), 'backend': 'python-reference',
            'code_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
        self.identity = digest(self.protocol)
        self._initialize()
        self.initial_objective = self.scorer.objective

    def _initialize(self):
        mode = self.config.initialization
        if mode == 'mixed':
            mode = ('frequency', 'lemma-aware', 'random')[self.restart % 3]
        mapping = self.candidates.initialize(self.segments, active_types=self.config.active_types,
                                            seed=self.rng.getrandbits(64), mode=mode)
        if self.config.injective:
            if len(mapping.assignments) > len(mapping.forms):
                raise ValueError('Injective search needs at least one candidate per active type')
            used = set()
            assignments = dict(mapping.assignments)
            available = [i for i in range(len(mapping.forms)) if i not in assignments.values()]
            self.rng.shuffle(available)
            for word, form in assignments.items():
                if form in used:
                    form = available.pop()
                    assignments[word] = form
                used.add(form)
            mapping = WordMapping(mapping.forms, assignments)
        self.scorer = IncrementalScorer(self.model, self.segments, mapping,
                                       collapse_weight=self.config.collapse_weight,
                                       frequency_weight=self.config.frequency_weight,
                                       injective=self.config.injective)
        self.mutations = MutationCatalog(mapping, self.candidates)
        self._archive()

    def _archive(self):
        if len(self.archive) == self.config.archive_size and self.scorer.objective < self.archive[-1]['score']:
            return
        assignments = dict(self.scorer.assignments)
        candidate = {'score': self.scorer.objective, 'assignments': assignments}
        near = [i for i, row in enumerate(self.archive) if
                sum(row['assignments'].get(w) != form for w, form in assignments.items())
                < self.config.archive_min_distance]
        if near:
            if max(self.archive[i]['score'] for i in near) >= candidate['score']:
                return
            self.archive = [row for i, row in enumerate(self.archive) if i not in near]
        self.archive.append(candidate)
        self.archive.sort(key=lambda row: (-row['score'], tuple(sorted(row['assignments'].items()))))
        del self.archive[self.config.archive_size:]

    @property
    def complete(self):
        return self.restart == self.config.restarts

    @property
    def best_mapping(self):
        return WordMapping(self.candidates.forms, dict(self.archive[0]['assignments']))

    def advance(self, evaluations=None):
        if evaluations is not None and (type(evaluations) is not int or evaluations < 0):
            raise ValueError('Evaluation budget must be nonnegative')
        remaining = evaluations
        operators = ('replace', 'swap', 'inflection', 'lemma')
        while not self.complete and (remaining is None or remaining > 0):
            fraction = self.step / max(1, self.config.steps_per_restart - 1)
            temperature = self.config.initial_temperature * (
                self.config.final_temperature / self.config.initial_temperature) ** fraction
            kind = self.rng.choices(operators, weights=self.config.mutation_weights)[0]
            kind, changes = self.mutations.propose(self.scorer, self.rng, kind)
            # Replacements into occupied forms become swaps. Both swaps and
            # replacements into unused forms keep every injective state reachable.
            if self.config.injective and len(changes) == 1:
                changes = injective_changes(self.scorer.assignments, changes)
                if len(changes) == 2:
                    kind = 'swap'
            proposal = self.scorer.propose(changes)
            delta = self.scorer.delta(proposal)
            self.statistics[kind]['proposed'] += 1
            if delta >= 0 or math.log(max(self.rng.random(), 1e-300)) < delta / temperature:
                self.scorer.commit(proposal)
                self.statistics[kind]['accepted'] += 1
                self.statistics[kind]['improved'] += delta > 0
                self._archive()
            self.step += 1
            self.evaluations += 1
            if remaining is not None:
                remaining -= 1
            if self.step == self.config.steps_per_restart:
                self.scorer.validate()
                self.restart += 1
                self.step = 0
                if not self.complete:
                    self._initialize()
        return self.best_mapping

    def checkpoint(self, path):
        self.scorer.validate()
        value = {'protocol': self.protocol, 'identity': self.identity,
            'restart': self.restart, 'step': self.step, 'evaluations': self.evaluations,
            'rng_state': self.rng.getstate(), 'statistics': self.statistics,
            'archive': self.archive, 'assignments': self.scorer.assignments,
            'initial_objective': self.initial_objective,
            'event_scores': self.scorer.event_scores, 'log_likelihood': self.scorer.log_likelihood,
            'frequency_penalty': self.scorer.frequency_penalty,
            'generation': self.scorer.generation}
        value['sha256'] = digest(value)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
                json.dump(value, handle, indent=2, ensure_ascii=False)
                handle.write('\n')
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def resume(self, path):
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        checksum = value.pop('sha256')
        if digest(value) != checksum:
            raise ValueError('Checkpoint checksum mismatch')
        if value['identity'] != self.identity or digest(value['protocol']) != self.identity:
            raise ValueError('Checkpoint protocol/model/config/split changed')
        scorer = IncrementalScorer(self.model, self.segments,
            WordMapping(self.candidates.forms, value['assignments']),
            collapse_weight=self.config.collapse_weight,
            frequency_weight=self.config.frequency_weight, injective=self.config.injective)
        if scorer.event_scores != value['event_scores']:
            raise ValueError('Checkpoint event cache mismatch')
        scorer.log_likelihood = value['log_likelihood']
        scorer.frequency_penalty = value['frequency_penalty']
        scorer.generation = value['generation']
        scorer.validate()
        self.scorer = scorer
        self.mutations = MutationCatalog(scorer.mapping, self.candidates)
        self.restart, self.step = value['restart'], value['step']
        self.evaluations = value['evaluations']
        self.rng.setstate(_tuples(value['rng_state']))
        self.archive, self.statistics = value['archive'], value['statistics']
        self.initial_objective = value['initial_objective']
        return self
