"""Bounded zero-corruption diagnostics; truth never enters blind-search modules."""
from collections import Counter
import hashlib
import math
from pathlib import Path

from .data.corpus import digest
from .widening_mapping import WideningSearch
from .word_mapping.incremental import IncrementalScorer
from .word_mapping.mapping import WordMapping
from .word_mapping.mutations import MutationCatalog

EPS = 1e-9


class OracleStartSearch(WideningSearch):
    """Initialize perfectly and evaluate every proposal's exact recovery delta.

    'annealing' retains the usual acceptance rule. 'greedy' accepts only strict
    score increases, excluding downhill annealing and score-equivalent drift.
    The oracle measures recovery; it is not the optimization objective.
    """
    def __init__(self, model, candidates, morphology, public, truth, config, *, policy='annealing'):
        if policy not in {'annealing', 'greedy'} or config.restarts != 1 or not config.injective:
            raise ValueError('One injective oracle start and a supported policy required')
        if public.identity != truth.public_sha256:
            raise ValueError('Truth/public identity differs')
        words = {w for s in public.segments for w in s}
        if words != set(truth.decoding):
            raise ValueError('Oracle dictionary must cover exactly the fit types')
        ids = {f: i for i, f in enumerate(candidates.forms)}
        if any(f not in ids for f in truth.decoding.values()):
            raise ValueError('Every true form must be in the candidate pool')
        self.gold = {w: ids[f] for w, f in truth.decoding.items()}
        mapping = WordMapping(candidates.forms, self.gold)
        if mapping.collapse_penalty or mapping.render(public.segments) != truth.plaintext:
            raise ValueError('Oracle dictionary is not an exact injective decoding')
        self.policy = policy
        self.word_counts = Counter(w for s in public.segments for w in s)
        self.total_tokens = sum(self.word_counts.values())
        self.correct_tokens, self.correct_types = self.total_tokens, len(self.gold)
        self.quality = {f'{score}/{recovery}': {'proposed': 0, 'accepted': 0}
            for score in ('up', 'flat', 'down') for recovery in ('up', 'flat', 'down')}
        self.first_departure = None
        self.perfect_score_witness = None
        super().__init__(model, candidates, morphology, public.segments, config, input_sha256=public.identity)
        self.protocol = {**self.protocol, 'oracle_initialization': 'exact dictionary; zero corruptions; no restarts',
            'oracle_dictionary_sha256': digest(self.gold), 'acceptance_policy': policy,
            'oracle_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        self.identity = digest(self.protocol)

    def _initialize(self):
        self.scorer = IncrementalScorer(self.model, self.segments, WordMapping(self.candidates.forms, self.gold),
            collapse_weight=self.config.collapse_weight, frequency_weight=self.config.frequency_weight, injective=True)
        self.mutations = MutationCatalog(self.scorer.mapping, self.candidates)
        self.owners = {f: w for w, f in self.gold.items()}
        self._archive()

    def advance(self, evaluations=None):
        if evaluations is not None and (type(evaluations) is not int or evaluations < 0):
            raise ValueError('Nonnegative proposal budget required')
        remaining = evaluations
        operators = ('replace', 'swap', 'inflection', 'lemma')
        while not self.complete and (remaining is None or remaining > 0):
            fraction = self.step / max(1, self.config.steps_per_restart-1)
            temperature = self.config.initial_temperature * (self.config.final_temperature/self.config.initial_temperature)**fraction
            kind = self.rng.choices(operators, weights=self.config.mutation_weights)[0]
            if kind == 'swap' and len(self.mutations.active) >= 2:
                left, right = self.rng.sample(self.mutations.active, 2)
                changes = {left: self.scorer.assignments[right], right: self.scorer.assignments[left]}
            else:
                kind, changes = self.mutations.propose(self.scorer, self.rng, kind)
            if len(changes) == 1:
                word, form = next(iter(changes.items()))
                owner = self.owners.get(form)
                if owner is not None and owner != word:
                    changes[owner] = self.scorer.assignments[word]
                    kind = 'swap'
            proposal = self.scorer.propose(changes)
            delta = self.scorer.delta(proposal)
            type_delta = sum(int(f == self.gold[w])-int(self.scorer.assignments[w] == self.gold[w])
                             for w, f in proposal.changes.items())
            token_delta = sum(self.word_counts[w] * (int(f == self.gold[w])-int(self.scorer.assignments[w] == self.gold[w]))
                              for w, f in proposal.changes.items())
            score_direction = 'up' if delta > EPS else ('down' if delta < -EPS else 'flat')
            recovery_direction = 'up' if token_delta > 0 else ('down' if token_delta < 0 else 'flat')
            quality = self.quality[f'{score_direction}/{recovery_direction}']
            quality['proposed'] += 1
            self.statistics[kind]['proposed'] += 1
            perfect = self.correct_tokens == self.total_tokens
            accepted = (delta > EPS) if self.policy == 'greedy' else (
                delta >= 0 or math.log(max(self.rng.random(), 1e-300)) < delta/temperature)
            if perfect and delta > EPS and token_delta < 0 and self.perfect_score_witness is None:
                self.perfect_score_witness = {'evaluation': self.evaluations+1, 'score_delta': delta,
                    'token_delta': token_delta, 'type_delta': type_delta,
                    'changes': dict(proposal.changes), 'accepted': accepted}
            if accepted:
                if perfect and token_delta < 0 and self.first_departure is None:
                    self.first_departure = {'evaluation': self.evaluations+1, 'score_delta': delta,
                        'token_delta': token_delta, 'type_delta': type_delta, 'changes': dict(proposal.changes)}
                for word in proposal.changes:
                    del self.owners[self.scorer.assignments[word]]
                self.scorer.commit(proposal)
                self.owners.update({form: word for word, form in proposal.changes.items()})
                self.correct_tokens += token_delta
                self.correct_types += type_delta
                quality['accepted'] += 1
                self.statistics[kind]['accepted'] += 1
                self.statistics[kind]['improved'] += delta > 0
                self._archive()
            self.step += 1
            self.evaluations += 1
            if remaining is not None:
                remaining -= 1
            if self.step == self.config.steps_per_restart:
                self.scorer.validate()
                self.validate_oracle()
                self.restart = 1
                self.step = 0
        return self.best_mapping

    def validate_oracle(self):
        types = sum(self.scorer.assignments[w] == f for w, f in self.gold.items())
        tokens = sum(self.word_counts[w] for w, f in self.gold.items() if self.scorer.assignments[w] == f)
        if (types, tokens) != (self.correct_types, self.correct_tokens):
            raise ValueError('Oracle accuracy counter drift')
        if self.owners != {f: w for w, f in self.scorer.assignments.items()}:
            raise ValueError('Inverse owner drift')
        if sum(v['proposed'] for v in self.quality.values()) != self.evaluations:
            raise ValueError('Proposal quality counts differ')
        if sum(v['accepted'] for v in self.quality.values()) != sum(v['accepted'] for v in self.statistics.values()):
            raise ValueError('Accepted quality counts differ')

    def checkpoint(self, path):
        raise NotImplementedError('Bounded oracle diagnostics use deterministic full replay')

    def resume(self, path):
        raise NotImplementedError('Bounded oracle diagnostics use deterministic full replay')
