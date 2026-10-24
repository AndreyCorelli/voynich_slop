"""Transactional sparse dictionary moves with every affected occurrence retained.

Equivalent cipher bigram events are aggregated with multiplicities. Their IDs
are deduplicated across changed types, not their number of scored occurrences.
There are no sentence resets, inactive types or objective-removing abstentions.
"""
from collections import Counter
from dataclasses import dataclass, field
import math

from .sparse_lm import BOS
from .state import DictionaryState, _word

EOS = -2  # Public event marker; distinct from all opaque cipher IDs.


@dataclass(frozen=True)
class EventIndex:
    cipher_sha256: str
    occurrences: tuple[tuple[tuple[int, int], ...], ...]
    events: tuple[tuple[int, ...], ...]  # Ngram + count, or graph (doc,a,b,count); contrast counts may be signed.
    affected: tuple[tuple[int, ...], ...]
    order: int = 2
    objective: str = "language_model"
    distances: tuple[int, ...] = (1,)
    objective_sha256: str | None = None

    @classmethod
    def build(cls, stream, *, order=2):
        if order not in (2,3):
            raise ValueError("Unsupported event order")
        occurrences = [[] for _ in range(stream.type_count)]
        counts = Counter()
        for doc_id, document in enumerate(stream.documents):
            previous = BOS
            before = BOS
            for position, cipher in enumerate(document):
                occurrences[cipher].append((doc_id, position))
                counts[(previous,cipher) if order == 2 else (before,previous,cipher)] += 1
                before,previous = previous,cipher
            counts[(previous,EOS) if order == 2 else (before,previous,EOS)] += 1
        events = tuple((*event,n) for event,n in sorted(counts.items()))
        affected = [[] for _ in range(stream.type_count)]
        for index, event in enumerate(events):
            for cipher in sorted(set(event[:-1]) - {BOS, EOS}):
                affected[cipher].append(index)
        return cls(stream.identity, tuple(map(tuple, occurrences)), events, tuple(map(tuple, affected)), order)


    @classmethod
    def build_association(cls, stream, distances):
        from .association import pair_counts
        occurrences=[[] for _ in range(stream.type_count)]
        events=[]
        for doc_id,document in enumerate(stream.documents):
            for position,cipher in enumerate(document): occurrences[cipher].append((doc_id,position))
            events.extend((doc_id,a,b,n) for (a,b),n in sorted(pair_counts(document,distances).items()))
        affected=[[] for _ in range(stream.type_count)]
        for i,(_,a,b,_) in enumerate(events):
            for cipher in sorted({a,b}): affected[cipher].append(i)
        return cls(stream.identity,tuple(map(tuple,occurrences)),tuple(events),tuple(map(tuple,affected)),
                   2,'association',tuple(distances))

    @classmethod
    def build_shuffle_contrast(cls,stream,model):
        occurrences=[[] for _ in range(stream.type_count)];events=[]
        for doc_id,document in enumerate(stream.documents):
            for position,cipher in enumerate(document):occurrences[cipher].append((doc_id,position))
            events.extend((doc_id,a,b,n) for (a,b),n in sorted(model.pairs(document).items()))
            if model.frequency_weight:
                events.extend((doc_id,BOS,c,n) for c,n in sorted(Counter(document).items()))
        affected=[[] for _ in range(stream.type_count)]
        for i,(_,a,b,_) in enumerate(events):
            for cipher in sorted({a,b}-{BOS}):affected[cipher].append(i)
        return cls(stream.identity,tuple(map(tuple,occurrences)),tuple(events),tuple(map(tuple,affected)),
                   2,'shuffle_contrast',(1,),model.identity)


def full_score(model, stream, state):
    """Independent occurrence-by-occurrence scorer, without event aggregation."""
    state.bind(stream, model)
    return math.fsum(model.score(state.assignments[c] for c in document) for document in stream.documents)


@dataclass(frozen=True)
class Move:
    generation: int
    changes: tuple[tuple[int, int], ...]
    event_scores: tuple[tuple[int, float], ...]
    log_delta: float
    _owner: object = field(repr=False, compare=False)


class DictionaryScorer:
    def __init__(self, model, stream, state, *, event_index=None):
        state.bind(stream, model)
        self.model, self.stream = model, stream
        order = getattr(model,'order',2)
        association = getattr(model,'objective_kind',None) == 'association'
        contrast = getattr(model,'objective_kind',None) == 'shuffle_contrast'
        objective = 'association' if association else ('shuffle_contrast' if contrast else 'language_model')
        distances = model.distances if association else (1,)
        if event_index is not None and (event_index.cipher_sha256 != state.cipher_sha256 or event_index.order != order
                                       or event_index.objective != objective or event_index.distances != distances
                                       or (contrast and event_index.objective_sha256 != model.identity)):
            raise ValueError('Event index belongs to a different cipher, model order or objective')
        self.index = event_index if event_index is not None else (
            EventIndex.build_shuffle_contrast(stream,model) if contrast else (
                EventIndex.build_association(stream,distances) if association else EventIndex.build(stream,order=order)))
        self._association_factors = {}
        if association:
            from .association import association_factors
            by_doc = {}
            for doc,a,b,n in self.index.events: by_doc.setdefault(doc,{})[a,b]=n
            for doc,pairs in by_doc.items():
                for (a,b),factor in association_factors(pairs,clip=model.clip,shrinkage=model.shrinkage).items():
                    self._association_factors[doc,a,b]=factor
        self._cipher_sha256 = state.cipher_sha256
        self._assignments = list(state.assignments)
        self._owners = {w: c for c, w in enumerate(state.assignments)}
        self._generation, self._token = 0, object()
        self._start_normalizer = math.log1p(-(model.probability(BOS, model.eos) if order == 2
                                                  else model.probability3(BOS,BOS,model.eos)))
        self._scores = [self._score_event(event, {}) for event in self.index.events]
        self._score = math.fsum(self._scores)

    @property
    def generation(self):
        return self._generation

    @property
    def score(self):
        return self._score

    @property
    def state(self):
        return DictionaryState(self._cipher_sha256, self.model.inventory_sha256,
                               self.model.size, tuple(self._assignments))

    def assignment(self, cipher):
        self._cipher(cipher)
        return self._assignments[cipher]

    def owner(self, word_id):
        _word(word_id, self.model.size)
        return self._owners.get(word_id)

    def _cipher(self, cipher):
        if type(cipher) is not int or not 0 <= cipher < self.stream.type_count:
            raise ValueError('Invalid cipher type ID')

    def _score_event(self, event, changes):
        if self.index.objective == 'shuffle_contrast':
            _,a,b,count=event
            word=changes.get(b,self._assignments[b])
            if a==BOS:return count*self.model.frequency_weight*math.log(self.model.base_probability(word))
            previous=changes.get(a,self._assignments[a])
            return count*self.model.pair_value(previous,word)/self.model.shuffles
        if self.index.objective == 'association':
            doc,a,b,count = event
            previous = changes.get(a,self._assignments[a])
            word = changes.get(b,self._assignments[b])
            target,weight = self._association_factors[doc,a,b]
            return -weight*(target-self.model.value(previous,word))**2
        if self.index.order == 3:
            a,b,c,count = event
            before = BOS if a == BOS else changes.get(a,self._assignments[a])
            previous = BOS if b == BOS else changes.get(b,self._assignments[b])
            word = self.model.eos if c == EOS else changes.get(c,self._assignments[c])
            logp = math.log(self.model._probability3(before,previous,word))
            if b == BOS:
                logp -= self._start_normalizer
            return count*logp
        a, b, count = event
        previous = BOS if a == BOS else changes.get(a, self._assignments[a])
        word = self.model.eos if b == EOS else changes.get(b, self._assignments[b])
        logp = math.log(self.model.probability(previous, word))
        if a == BOS:
            logp -= self._start_normalizer
        adjustment = getattr(self.model, "score_adjustment", None)
        if adjustment is not None:
            logp += adjustment(word)
        return count * logp

    def propose(self, changes):
        """Build a move without mutation. Discarding it rejects it.

        Validation touches only changed rows and reverse owners. Atomic cycles
        are allowed; replacing a row with another row's form requires moving
        that owner too. Merely preparing a move cannot change a later proposal.
        """
        changes = dict(changes)
        for cipher, word in changes.items():
            self._cipher(cipher)
            _word(word, self.model.size)
        changed = {c: w for c, w in changes.items() if w != self._assignments[c]}
        if len(set(changed.values())) != len(changed):
            raise ValueError('Move would violate injectivity')
        for word in changed.values():
            other = self._owners.get(word)
            if other is not None and other not in changed:
                raise ValueError('Move targets an occupied surface; use a swap')
        affected = sorted({i for c in changed for i in self.index.affected[c]})
        scores = tuple((i, self._score_event(self.index.events[i], changed)) for i in affected)
        delta = math.fsum(score - self._scores[i] for i, score in scores)
        return Move(self.generation, tuple(sorted(changed.items())), scores, delta, self._token)

    def replace(self, cipher, word):
        return self.propose({cipher: word})

    def swap(self, first, second):
        self._cipher(first)
        self._cipher(second)
        return self.propose({first: self._assignments[second], second: self._assignments[first]})

    def assign_or_swap(self, cipher, word):
        self._cipher(cipher)
        _word(word, self.model.size)
        other = self._owners.get(word)
        return self.swap(cipher, other) if other is not None else self.replace(cipher, word)

    def commit(self, move):
        if move._owner is not self._token or move.generation != self.generation:
            raise ValueError('Stale or foreign dictionary move')
        # Remove all old owners before inserting new ones, so swaps are atomic.
        for cipher, _ in move.changes:
            del self._owners[self._assignments[cipher]]
        for cipher, word in move.changes:
            self._assignments[cipher] = word
            self._owners[word] = cipher
        for index, score in move.event_scores:
            self._scores[index] = score
        self._score += move.log_delta
        self._generation += 1

    def validate(self, *, tolerance=1e-8):
        state = self.state  # Also checks completeness/injectivity.
        if self._owners != {w: c for c, w in enumerate(state.assignments)}:
            raise ValueError('Reverse ownership drift')
        expected = full_score(self.model, self.stream, state)
        if abs(expected - self.score) > tolerance:
            raise ValueError('Incremental score drift')
        scores = [self._score_event(event, {}) for event in self.index.events]
        if any(abs(a - b) > tolerance for a, b in zip(scores, self._scores)):
            raise ValueError('Event score drift')
        return expected
