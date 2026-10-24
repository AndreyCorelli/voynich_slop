"""Transactional local scoring for a fixed active ciphertext vocabulary."""
from collections import Counter
from dataclasses import dataclass
import math

from .mapping import WordMapping
from .ngram import BOS, EOS, OOV
from .objective import frequency_penalty, frequency_term, training_probabilities


@dataclass(frozen=True)
class Proposal:
    generation: int
    changes: dict
    event_scores: dict
    log_delta: float
    count_delta: dict
    penalty_delta: int
    token_count_delta: dict
    frequency_delta: float


class IncrementalScorer:
    def __init__(self, model, segments, mapping, *, collapse_weight=0.0,
                 frequency_weight=0.0, injective=False):
        if not math.isfinite(collapse_weight) or collapse_weight < 0:
            raise ValueError('Collapse weight must be finite and nonnegative')
        if not math.isfinite(frequency_weight) or frequency_weight < 0:
            raise ValueError('Frequency weight must be finite and nonnegative')
        if type(injective) is not bool or (injective and mapping.collapse_penalty):
            raise ValueError('Invalid injective dictionary')
        self.model = model
        self.segments = tuple(tuple(s) for s in segments)
        self.forms = mapping.forms
        self.assignments = dict(mapping.assignments)
        self.form_ids = tuple(model.form_ids.get(w, OOV) for w in self.forms)
        self.collapse_weight = collapse_weight
        self.frequency_weight, self.injective = frequency_weight, injective
        self.word_counts = Counter(w for s in self.segments for w in s)
        self.token_counts = Counter()
        for word, form in self.assignments.items():
            if form is not None:
                self.token_counts[form] += self.word_counts[word]
        self.active_tokens = sum(self.token_counts.values())
        self.probabilities = training_probabilities(model, self.forms)
        self.frequency_penalty = frequency_penalty(model, self.segments, mapping)
        self.counts = Counter(v for v in self.assignments.values() if v is not None)
        self.penalty = mapping.collapse_penalty
        self.events = []
        self.affected = {}
        self.generation = 0
        self.log_cache = {}
        # Event terms are ciphertext word names, or BOS/EOS constants. A single
        # word may occur more than once in one event; deduplicate dependencies.
        for segment in self.segments:
            a = b = BOS
            active = False
            for word in segment:
                if self.assignments.get(word) is None:
                    if active:
                        self._add_event((a, b, EOS))
                    a = b = BOS
                    active = False
                    continue
                self._add_event((a, b, word))
                a, b = b, word
                active = True
            if active:
                self._add_event((a, b, EOS))
        self.event_scores = [self._score_event(event, {}) for event in self.events]
        self.log_likelihood = math.fsum(self.event_scores)

    def _add_event(self, event):
        index = len(self.events)
        self.events.append(event)
        for word in set(term for term in event if isinstance(term, str)):
            self.affected.setdefault(word, set()).add(index)

    def _score_event(self, event, changes):
        ids = [term if isinstance(term, int) else
               self.form_ids[changes.get(term, self.assignments[term])] for term in event]
        key = tuple(ids)
        if key not in self.log_cache:
            if len(self.log_cache) >= 100000:
                self.log_cache.clear()
            self.log_cache[key] = math.log(self.model.probability(*ids))
        return self.log_cache[key]

    @property
    def objective(self):
        return (self.log_likelihood - self.collapse_weight * self.penalty
                - self.frequency_weight * self.frequency_penalty)

    @property
    def mapping(self):
        return WordMapping(self.forms, dict(self.assignments))

    def propose(self, changes):
        changes = dict(changes)
        for word, form in changes.items():
            if self.assignments.get(word) is None:
                raise ValueError('Cannot mutate inactive/UNKNOWN types')
            if type(form) is not int or not 0 <= form < len(self.forms):
                raise ValueError('Mutation must assign a valid surface ID')
        changed = {word: form for word, form in changes.items() if self.assignments[word] != form}
        affected = set()
        counts = Counter()
        token_counts = Counter()
        for word, form in changed.items():
            affected.update(self.affected.get(word, ()))
            counts[self.assignments[word]] -= 1
            counts[form] += 1
            token_counts[self.assignments[word]] -= self.word_counts[word]
            token_counts[form] += self.word_counts[word]
        scores = {index: self._score_event(self.events[index], changed) for index in sorted(affected)}
        delta = math.fsum(score - self.event_scores[index] for index, score in scores.items())
        penalty_delta = sum(max(0, self.counts[form] + count - 1) - max(0, self.counts[form] - 1)
                            for form, count in counts.items())
        if self.injective and self.penalty + penalty_delta:
            raise ValueError('Proposal violates injective constraint')
        frequency_delta = math.fsum(
            frequency_term(self.token_counts[form] + count, self.active_tokens, self.probabilities[form])
            - frequency_term(self.token_counts[form], self.active_tokens, self.probabilities[form])
            for form, count in token_counts.items())
        return Proposal(self.generation, changed, scores, delta, dict(counts), penalty_delta,
                        dict(token_counts), frequency_delta)

    def delta(self, proposal):
        return (proposal.log_delta - self.collapse_weight * proposal.penalty_delta
                - self.frequency_weight * proposal.frequency_delta)

    def commit(self, proposal):
        if proposal.generation != self.generation:
            raise ValueError('Stale scoring proposal')
        self.assignments.update(proposal.changes)
        self.counts.update(proposal.count_delta)
        self.penalty += proposal.penalty_delta
        self.token_counts.update(proposal.token_count_delta)
        self.frequency_penalty += proposal.frequency_delta
        for index, score in proposal.event_scores.items():
            self.event_scores[index] = score
        self.log_likelihood += proposal.log_delta
        self.generation += 1

    def validate(self):
        score = self.model.score(self.mapping.render(self.segments))
        if not math.isclose(score.log_likelihood, self.log_likelihood, rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError('Incremental likelihood drift')
        if self.mapping.collapse_penalty != self.penalty:
            raise ValueError('Collapse count drift')
        full_penalty = frequency_penalty(self.model, self.segments, self.mapping)
        if not math.isclose(full_penalty, self.frequency_penalty, rel_tol=1e-12, abs_tol=1e-8):
            raise ValueError('Frequency penalty drift')
        if self.injective and self.penalty:
            raise ValueError('Injective constraint drift')
        return score
