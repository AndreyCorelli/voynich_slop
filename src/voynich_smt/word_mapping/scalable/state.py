"""Complete injective dictionary snapshots and sparse initialization.

Only observed cipher types have assignments. Inventory strings are not copied
into states, and initialization never allocates a type-by-inventory matrix.
"""
from collections import Counter, deque
from dataclasses import dataclass
import random


class CandidateConflict(ValueError):
    """The supplied sparse candidate graph has no complete injective matching."""


def _word(word, inventory_size):
    if type(word) is not int or not 0 <= word < inventory_size:
        raise ValueError('Invalid surface inventory ID')


@dataclass(frozen=True)
class DictionaryState:
    cipher_sha256: str
    inventory_sha256: str
    inventory_size: int
    assignments: tuple[int, ...]  # Indexed by opaque cipher ID.

    def __post_init__(self):
        object.__setattr__(self, 'assignments', tuple(self.assignments))
        if type(self.inventory_size) is not int or self.inventory_size < 1 or not self.assignments:
            raise ValueError('Expected a nonempty dictionary and inventory')
        for w in self.assignments:
            _word(w, self.inventory_size)
        if len(set(self.assignments)) != len(self.assignments):
            raise ValueError('Dictionary must be injective')
        if not self.cipher_sha256 or not self.inventory_sha256:
            raise ValueError('Dictionary requires public resource identities')

    @classmethod
    def create(cls, stream, model, assignments):
        result = cls(stream.identity, model.inventory_sha256, model.size, assignments)
        result.bind(stream, model)
        return result

    def bind(self, stream, model):
        if stream.tokenization != getattr(getattr(model, "config", None), "tokenization", stream.tokenization):
            raise ValueError("Cipher/model tokenization mismatch")
        if (self.cipher_sha256 != stream.identity or self.inventory_sha256 != model.inventory_sha256
                or self.inventory_size != model.size or len(self.assignments) != stream.type_count):
            raise ValueError('Dictionary does not match public cipher/model resources')

    @classmethod
    def random(cls, stream, model, *, seed):
        if model.size < stream.type_count:
            raise ValueError('Inventory is smaller than observed cipher vocabulary')
        return cls.create(stream, model, random.Random(seed).sample(range(model.size), stream.type_count))

    @classmethod
    def frequency(cls, stream, model):
        """Align public type counts with source unigram ranks; no plaintext access."""
        if model.size < stream.type_count:
            raise ValueError('Inventory is smaller than observed cipher vocabulary')
        counts = Counter(c for document in stream.documents for c in document)
        cipher_rank = sorted(counts, key=lambda c: (-counts[c], c))
        source_rank = sorted(range(model.size), key=lambda w: (-model.counts[w], w))
        assignments = [0] * stream.type_count
        for cipher, word in zip(cipher_rank, source_rank):
            assignments[cipher] = word
        return cls.create(stream, model, assignments)

    @classmethod
    def initialize(cls, stream, model, *, method='random', seed=0):
        if method == 'random':
            return cls.random(stream, model, seed=seed)
        if method == 'classes':
            from .class_decode import initialize_classes
            if not hasattr(model, 'class_lm'): raise ValueError('Class initialization requires learned-class model')
            return initialize_classes(stream, model, seed=seed)
        if method == 'profile':
            from .profiles import initialize_profile
            return initialize_profile(stream, model, seed=seed)
        if method == 'frequency':
            return cls.frequency(stream, model)
        raise ValueError('Unknown dictionary initialization')

    @classmethod
    def from_candidates(cls, stream, model, candidates):
        """Find a full sparse matching, or raise without returning a partial key.

        Iterative augmenting paths avoid recursion depth depending on type count.
        Lists are tried in supplied preference order; this is feasibility matching,
        not maximum-weight assignment or a decipherment algorithm. On conflict,
        the retrieval layer must expand support explicitly.
        """
        if model.size < stream.type_count:
            raise ValueError('Inventory is smaller than observed cipher vocabulary')
        rows = tuple(tuple(dict.fromkeys(row)) for row in candidates)
        if len(rows) != stream.type_count:
            raise ValueError('Expected a candidate row for every cipher type')
        for row in rows:
            for w in row:
                _word(w, model.size)
        assignments, owner = {}, {}
        for root in range(stream.type_count):
            queue, parent, seen_words = deque([root]), {root: None}, set()
            found = None
            while queue and found is None:
                cipher = queue.popleft()
                for word in rows[cipher]:
                    if word in seen_words:
                        continue
                    seen_words.add(word)
                    other = owner.get(word)
                    if other is None:
                        found = cipher, word
                        break
                    if other not in parent:
                        parent[other] = cipher, word
                        queue.append(other)
            if found is None:
                raise CandidateConflict(f'No complete sparse matching; failed at cipher type {root}')
            cipher, word = found
            while True:
                assignments[cipher], owner[word] = word, cipher
                if parent[cipher] is None:
                    break
                cipher, word = parent[cipher]
        return cls.create(stream, model, (assignments[c] for c in range(stream.type_count)))
