"""Fixed-objective widening experiments, with efficient injective proposals."""
from collections import Counter
import hashlib
import math
from pathlib import Path

from .bootstrap_mapping import BootstrapOptions, BootstrapSearch
from .data.corpus import digest
from .word_mapping.ngram import NgramModel


def expanded_model(model, forms):
    """Add distinct zero-count surface IDs without adding any training events.

    This changes smoothing normalization. Use the same expanded model in every
    comparison arm. All zero-count surfaces remain statistically exchangeable.
    """
    extra = sorted(set(forms) - set(model.vocabulary))
    return NgramModel(model.vocabulary + tuple(extra), model.unigram,
                      model.bigram, model.trigram, model.config, model.training_sha256)


def nested_prefixes(segments, targets, *, holdout_tokens):
    """Whole-segment nested prefixes and a disjoint fixed final holdout."""
    segments = tuple(tuple(s) for s in segments if s)
    targets = tuple(targets)
    if (not targets or any(type(t) is not int or t < 1 for t in targets)
            or list(targets) != sorted(set(targets))
            or type(holdout_tokens) is not int or holdout_tokens < 1):
        raise ValueError('Increasing positive targets and positive holdout required')
    count = end_segments = 0
    for segment in reversed(segments):
        count += len(segment)
        end_segments += 1
        if count >= holdout_tokens:
            break
    available = segments[:-end_segments]
    if count < holdout_tokens or sum(map(len, available)) < targets[-1]:
        raise ValueError('Insufficient disjoint fit and holdout text')
    prefixes = {}
    for target in targets:
        count = 0
        for end, segment in enumerate(available, 1):
            count += len(segment)
            if count >= target:
                prefixes[target] = available[:end]
                break
    return prefixes, segments[-end_segments:]


def repetition_statistics(segments, holdout):
    counts = Counter(w for s in segments for w in s)
    held = Counter(w for s in holdout for w in s)
    return {'tokens': sum(counts.values()), 'types': len(counts),
        'occurrences_per_type': sum(counts.values()) / len(counts),
        'singleton_types': sum(n == 1 for n in counts.values()),
        'repeat_token_fraction': sum(n for n in counts.values() if n >= 2) / sum(counts.values()),
        'holdout_tokens': sum(held.values()),
        'holdout_recurring_tokens': sum(n for w, n in held.items() if w in counts),
        'holdout_unseen_types': len(held.keys() - counts.keys())}


class WideningSearch(BootstrapSearch):
    """Same four proposal families with O(1) injective owner lookup.

    A uniform ordered swap replaces the legacy linear active.index lookup.
    Scores, cooling and independent initialization streams are unchanged.
    """
    def __init__(self, model, candidates, morphology, segments, config, *, input_sha256=None):
        super().__init__(model, candidates, morphology, segments, config,
                         BootstrapOptions(), input_sha256=input_sha256)
        self.protocol = {**self.protocol,
            'widening_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'proposal_policy': 'four legacy operators; uniform ordered swap; cached inverse owners'}
        self.identity = digest(self.protocol)

    def _initialize(self):
        super()._initialize()
        self.owners = {form: word for word, form in self.scorer.assignments.items()}

    def resume(self, path):
        super().resume(path)
        self.owners = {form: word for word, form in self.scorer.assignments.items()}
        return self

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
            self.statistics[kind]['proposed'] += 1
            if delta >= 0 or math.log(max(self.rng.random(), 1e-300)) < delta / temperature:
                for word in proposal.changes:
                    del self.owners[self.scorer.assignments[word]]
                self.scorer.commit(proposal)
                self.owners.update({form: word for word, form in proposal.changes.items()})
                self.statistics[kind]['accepted'] += 1
                self.statistics[kind]['improved'] += delta > 0
                self._archive()
            self.step += 1
            self.evaluations += 1
            if remaining is not None:
                remaining -= 1
            if self.step == self.config.steps_per_restart:
                self.scorer.validate()
                if self.owners != {form: word for word, form in self.scorer.assignments.items()}:
                    raise ValueError('Owner cache drift')
                self.restart += 1
                self.step = 0
                if not self.complete:
                    self._initialize()
        return self.best_mapping
