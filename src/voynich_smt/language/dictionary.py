from dataclasses import dataclass

from voynich_smt.cipher.base import Bounds
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text


@dataclass(frozen=True)
class WordDictionary:
    """A finite token vocabulary, not a claim that arbitrary members form Latin."""

    words: tuple[tuple[str, ...], ...]

    def __post_init__(self):
        if not self.words or len(set(self.words)) != len(self.words):
            raise ValueError("Dictionary must be nonempty and contain unique words")
        Text(self.words)  # Validate tokens and reject empty words.

    @classmethod
    def from_strings(cls, words: tuple[str, ...]) -> "WordDictionary":
        if any(not w or any(c.isspace() for c in w) for w in words):
            raise ValueError("Each dictionary entry must be a single nonempty word")
        return cls(tuple(tuple(w) for w in words))

    def validate(self, alphabet: Alphabet) -> None:
        Text(self.words).validate(alphabet)

    def accepts(self, text: Text) -> bool:
        vocabulary = set(self.words)
        return all(word in vocabulary for word in text.words)

    def candidates(self, ciphertext_length: int, bounds: Bounds,
                   min_word_length: int, max_word_length: int) -> tuple[tuple[str, ...], ...]:
        """Prune only by public length bounds and observed ciphertext size."""
        return tuple(w for w in self.words
                     if min_word_length <= len(w) <= max_word_length
                     and len(w) * bounds.min_code_length <= ciphertext_length
                     <= len(w) * bounds.max_code_length)

    def candidate_graph(self, ciphertext: Text, bounds: Bounds,
                        min_word_length: int, max_word_length: int) -> "CandidateGraph":
        """Sound arc consistency from public ciphertext prefixes and unique decoding.

        A common prefix of K * maximum-code-length tokens guarantees at least K
        identical decoded tokens. A complete ciphertext word that prefixes another
        guarantees a strict plaintext-word prefix. No suffix inference is made.
        """
        candidates = [self.candidates(len(w), bounds, min_word_length, max_word_length)
                      for w in ciphertext.words]
        initial_count = sum(map(len, candidates))
        relations = []
        for left, a in enumerate(ciphertext.words):
            for right in range(left + 1, len(ciphertext.words)):
                b = ciphertext.words[right]
                common = 0
                for x, y in zip(a, b):
                    if x != y:
                        break
                    common += 1
                shared = common // bounds.max_code_length
                prefix = ("equal" if a == b else "left" if common == len(a)
                          else "right" if common == len(b) else None)
                if shared or prefix is not None:
                    relations.append(PrefixRelation(left, right, shared, prefix))
        changed = True
        while changed:
            changed = False
            for relation in relations:
                a, b = candidates[relation.left], candidates[relation.right]
                keep_a, keep_b = relation.prune(a, b)
                if keep_a != a or keep_b != b:
                    candidates[relation.left], candidates[relation.right] = keep_a, keep_b
                    changed = True
        return CandidateGraph(tuple(candidates), tuple(relations),
                              initial_count - sum(map(len, candidates)))


@dataclass(frozen=True)
class PrefixRelation:
    left: int
    right: int
    shared_tokens: int
    prefix: str | None

    def prune(self, a, b):
        """Preserve ordered arc pruning using indexed support membership."""
        left = {"left": "shorter", "right": "longer"}.get(self.prefix, self.prefix)
        right = {"left": "longer", "right": "shorter"}.get(self.prefix, self.prefix)
        keep_a = _supported_words(a, b, self.shared_tokens, left)
        keep_b = _supported_words(b, keep_a, self.shared_tokens, right)
        return keep_a, keep_b

    def accepts(self, a: tuple[str, ...], b: tuple[str, ...]) -> bool:
        if a[:self.shared_tokens] != b[:self.shared_tokens]:
            return False
        if self.prefix == "equal":
            return a == b
        if self.prefix == "left":
            return len(a) < len(b) and a == b[:len(a)]
        if self.prefix == "right":
            return len(b) < len(a) and b == a[:len(b)]
        return True


@dataclass(frozen=True)
class CandidateGraph:
    candidates: tuple[tuple[tuple[str, ...], ...], ...]
    relations: tuple[PrefixRelation, ...]
    pruned_candidates: int


def _supported_words(words, support, shared, kind):
    if kind == "equal":
        index = set(support)
        return tuple(w for w in words if w in index)
    if kind == "shorter":
        # A strict prefix shorter than `shared` cannot have equal shared slices.
        index = {w[:size] for w in support
                 for size in range(max(1, shared), len(w))}
        return tuple(w for w in words if w in index)
    if kind == "longer":
        index = set(support)
        return tuple(w for w in words if any(w[:size] in index
                     for size in range(max(1, shared), len(w))))
    index = {w[:shared] for w in support}
    return tuple(w for w in words if w[:shared] in index)
