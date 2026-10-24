"""Experimental uncertain proposals, weak agreement, and coordinated search.

No truth inputs, parsing claims, hard candidate exclusions or confidence locks.
Legacy word_mapping modules remain unchanged for frozen experiment replay.
"""
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import heapq
import math
from pathlib import Path
import random

from .data.corpus import digest
from .word_mapping.annealing import Annealer
from .word_mapping.mapping import WordMapping
from .word_mapping.mutations import injective_changes


@dataclass(frozen=True)
class BootstrapOptions:
    shortlist_probability: float = 0.0
    shortlist_size: int = 32
    agreement_weight: float = 0.0
    joint_probability: float = 0.0

    def __post_init__(self):
        for name in ('shortlist_probability', 'joint_probability'):
            value = getattr(self, name)
            if not math.isfinite(value) or not 0 <= value < 1:
                raise ValueError('Proposal probabilities must be finite in [0, 1)')
        if type(self.shortlist_size) is not int or self.shortlist_size < 1:
            raise ValueError('Positive shortlist size required')
        if not math.isfinite(self.agreement_weight) or self.agreement_weight < 0:
            raise ValueError('Agreement weight must be finite and nonnegative')


class AgreementModel:
    """Adjacent noun/modifier compatibility averaged over unique analyses.

    POS alternatives outside N versus ADJ/VPAR contribute zero. Unknown
    features are neutral; common gender C matches M/F, not neuter N.
    Uniform analysis weights are a heuristic, not a posterior or a parse.
    """
    def __init__(self, morphology):
        self.morphology_sha256 = morphology.identity
        self.signatures = {}
        for word, entries in morphology.entries.items():
            signatures = set()
            for entry in entries:
                for inflection in entry['inflections']:
                    features = inflection['features']
                    signatures.add((inflection['part_of_speech'],
                        features.get('Case', 'X'), features.get('Number', 'X'), features.get('Gender', 'X')))
            self.signatures[word] = tuple(sorted(signatures))
        self.cache = {}

    @staticmethod
    def compatible(a, b):
        if not ((a[0] == 'N' and b[0] in {'ADJ', 'VPAR'}) or (b[0] == 'N' and a[0] in {'ADJ', 'VPAR'})):
            return 0.0
        tests = []
        for index in (1, 2, 3):
            x, y = a[index], b[index]
            if x in {'X', ''} or y in {'X', ''}:
                continue
            tests.append(x == y or (index == 3 and {x, y} <= {'C', 'M', 'F'} and 'C' in {x, y}))
        return (1.0 if all(tests) else -1.0) if tests else 0.0

    def pair(self, left, right):
        key = (left, right)
        if key not in self.cache:
            a, b = self.signatures.get(left, ()), self.signatures.get(right, ())
            value = math.fsum(self.compatible(x, y) for x in a for y in b) / (len(a) * len(b)) if a and b else 0.0
            if len(self.cache) >= 100000:
                self.cache.clear()
            self.cache[key] = value
        return self.cache[key]

    def score(self, segments):
        return math.fsum(self.pair(a, b) for segment in segments for a, b in zip(segment, segment[1:]))


@dataclass(frozen=True)
class AgreementProposal:
    base: object
    scores: dict
    agreement_delta: float


class AgreementScorer:
    """Transactional local agreement factors around the existing local scorer."""
    def __init__(self, base, model, weight):
        self.base, self.agreement_model, self.weight = base, model, weight
        self.edges = [(a, b) for segment in base.segments for a, b in zip(segment, segment[1:])
            if base.assignments.get(a) is not None and base.assignments.get(b) is not None]
        self.affected_edges = {}
        for i, edge in enumerate(self.edges):
            for word in set(edge):
                self.affected_edges.setdefault(word, set()).add(i)
        self.agreement_scores = [self._score(edge, {}) for edge in self.edges]
        self.agreement_score = math.fsum(self.agreement_scores)

    def __getattr__(self, name):
        return getattr(self.base, name)

    def _score(self, edge, changes):
        return self.agreement_model.pair(*(self.forms[changes.get(w, self.assignments[w])] for w in edge))

    @property
    def objective(self):
        return self.base.objective + self.weight * self.agreement_score

    def propose(self, changes):
        base = self.base.propose(changes)
        affected = set().union(*(self.affected_edges.get(w, set()) for w in base.changes)) if base.changes else set()
        scores = {i: self._score(self.edges[i], base.changes) for i in sorted(affected)}
        delta = math.fsum(v - self.agreement_scores[i] for i, v in scores.items())
        return AgreementProposal(base, scores, delta)

    def delta(self, proposal):
        return self.base.delta(proposal.base) + self.weight * proposal.agreement_delta

    def commit(self, proposal):
        self.base.commit(proposal.base)  # Checks the generation before any writes.
        for i, value in proposal.scores.items():
            self.agreement_scores[i] = value
        self.agreement_score += proposal.agreement_delta

    def validate(self):
        result = self.base.validate()
        full = self.agreement_model.score(self.mapping.render(self.segments))
        if not math.isclose(full, self.agreement_score, abs_tol=1e-9, rel_tol=1e-12):
            raise ValueError('Agreement cache drift')
        return result


def coordinated_changes(assignments, desired):
    """Complete simultaneous replacements by moving displaced outside owners.

    At most two outside owners are displaced by a two-word joint replacement.
    They receive vacated old forms deterministically, preserving injectivity.
    """
    desired = dict(desired)
    if any(w not in assignments or assignments[w] is None or f is None for w, f in desired.items()):
        raise ValueError('Joint changes require active assignments')
    owners = {f: w for w, f in assignments.items()}
    if len(owners) != len(assignments) or len(set(desired.values())) != len(desired):
        raise ValueError('Joint changes require injective dictionaries and targets')
    outside = sorted({owners[f] for f in desired.values() if f in owners and owners[f] not in desired})
    vacated = sorted(set(assignments[w] for w in desired) - set(desired.values()))
    if len(outside) > len(vacated):
        raise ValueError('Not enough vacated forms')
    desired.update({w: f for w, f in zip(outside, vacated)})
    return desired


class BootstrapSearch(Annealer):
    def __init__(self, model, candidates, morphology, segments, config, options=BootstrapOptions(), *, input_sha256=None):
        if not config.injective:
            raise ValueError('Bootstrap prototype requires injective search')
        if morphology.training_sha256 != candidates.training_sha256 or morphology.identity != candidates.morphology_sha256:
            raise ValueError('Morphology/candidate training identity differs')
        self.options = options
        self.agreement = AgreementModel(morphology)
        segments = tuple(tuple(s) for s in segments)
        self.joint_edges = tuple((a, b) for s in segments for a, b in zip(s, s[1:]) if a != b)
        counts = Counter(w for s in segments for w in s)
        total = sum(counts.values())
        train_total = sum(candidates.form_counts.values()) + len(candidates.forms) * model.config.alpha
        logp = [math.log((candidates.form_counts[w] + model.config.alpha) / train_total) for w in candidates.forms]
        self.prior_weights, self.shortlists = {}, {}
        if options.shortlist_probability:
            for word, count in counts.items():
                distances = [abs(p - math.log(count / total)) for p in logp]
                self.shortlists[word] = tuple(heapq.nsmallest(options.shortlist_size, range(len(logp)), key=lambda i: (distances[i], i)))
                self.prior_weights[word] = tuple(math.exp(-d) for d in distances)
        super().__init__(model, candidates, segments, config, input_sha256=input_sha256)
        self.statistics.update({kind: {'proposed': 0, 'accepted': 0, 'improved': 0} for kind in ('shortlist', 'joint')})
        self.protocol = {**self.protocol, 'bootstrap_options': asdict(options),
            'morphology_sha256': morphology.identity,
            'initialization_policy': 'independent deterministic stream for each restart; shared across arms',
            'bootstrap_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        self.identity = digest(self.protocol)

    def _initialize(self):
        # Separate streams keep starting dictionaries paired across ablations.
        previous = self.rng
        seed = int(digest({'seed': self.config.seed, 'restart': self.restart, 'purpose': 'bootstrap-init'})[:16], 16)
        self.rng = random.Random(seed)
        try:
            super()._initialize()
            active = set(self.mutations.active)
            self.active_joint_edges = tuple((a, b) for a, b in self.joint_edges if a in active and b in active)
        finally:
            self.rng = previous

    def _archive(self):
        if self.options.agreement_weight and not isinstance(self.scorer, AgreementScorer):
            self.scorer = AgreementScorer(self.scorer, self.agreement, self.options.agreement_weight)
        super()._archive()

    def candidate_ids(self, word):
        support = Counter(row['assignments'][word] for row in self.archive)
        ids = tuple(sorted(set(self.shortlists[word]) | set(support)))
        weights = [self.prior_weights[word][i] + support[i] / max(1, len(self.archive)) for i in ids]
        return ids, weights

    def _draw(self, word):
        if self.options.shortlist_probability and self.rng.random() < self.options.shortlist_probability:
            ids, weights = self.candidate_ids(word)
            return self.rng.choices(ids, weights=weights)[0]
        return self.rng.randrange(len(self.candidates.forms))

    def _joint(self):
        if not self.active_joint_edges:
            return 'replace', {self.rng.choice(self.mutations.active): self.rng.randrange(len(self.candidates.forms))}
        left, right = self.rng.choice(self.active_joint_edges)
        first = self._draw(left)
        second = self._draw(right)
        for _ in range(16):
            if first != second:
                break
            second = self._draw(right)
        if first == second:
            return 'swap', {left: self.scorer.assignments[right], right: self.scorer.assignments[left]}
        return 'joint', coordinated_changes(self.scorer.assignments, {left: first, right: second})

    def advance(self, evaluations=None):
        if evaluations is not None and (type(evaluations) is not int or evaluations < 0):
            raise ValueError('Evaluation budget must be nonnegative')
        remaining = evaluations
        operators = ('replace', 'swap', 'inflection', 'lemma')
        while not self.complete and (remaining is None or remaining > 0):
            fraction = self.step / max(1, self.config.steps_per_restart - 1)
            temperature = self.config.initial_temperature * (self.config.final_temperature / self.config.initial_temperature) ** fraction
            if self.options.joint_probability and self.rng.random() < self.options.joint_probability:
                kind, changes = self._joint()
            elif self.options.shortlist_probability and self.rng.random() < self.options.shortlist_probability:
                word = self.rng.choice(self.mutations.active)
                ids, weights = self.candidate_ids(word)
                kind, changes = 'shortlist', {word: self.rng.choices(ids, weights=weights)[0]}
            else:
                kind = self.rng.choices(operators, weights=self.config.mutation_weights)[0]
                kind, changes = self.mutations.propose(self.scorer, self.rng, kind)
            if len(changes) == 1:
                changes = injective_changes(self.scorer.assignments, changes)
                # Keep the origin label for shortlist proposals, including owner swaps.
                if len(changes) == 2 and kind != 'shortlist':
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

    def resume(self, path):
        super().resume(path)
        if self.options.agreement_weight:
            self.scorer = AgreementScorer(self.scorer, self.agreement, self.options.agreement_weight)
        self.scorer.validate()
        active = set(self.mutations.active)
        self.active_joint_edges = tuple((a, b) for a, b in self.joint_edges if a in active and b in active)
        return self

    def hypotheses(self):
        """Archive support is descriptive and is not calibrated confidence."""
        result = {}
        for word in sorted(self.scorer.assignments):
            counts = Counter(r['assignments'][word] for r in self.archive)
            alternatives = [{'surface': self.candidates.forms[i], 'archive_support': n / len(self.archive)}
                for i, n in sorted(counts.items(), key=lambda r: (-r[1], r[0]))]
            result[word] = {'alternatives': alternatives, 'locked': False}
        return result
