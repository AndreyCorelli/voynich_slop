from dataclasses import dataclass
import random

from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text

Code = tuple[str, ...]


@dataclass(frozen=True)
class NullInsertion:
    """A glyph at an absolute observed position in a word."""

    word: int
    position: int
    symbol: str


@dataclass(frozen=True)
class Bounds:
    family: str = "verbose"
    max_homophones: int = 2
    min_code_length: int = 1
    max_code_length: int = 3

    def __post_init__(self):
        if self.family not in {"monoalphabetic", "homophonic", "verbose"}:
            raise ValueError("Unknown cipher family")
        if self.max_homophones < 1 or not 1 <= self.min_code_length <= self.max_code_length:
            raise ValueError("Invalid bounds")
        if self.family == "monoalphabetic" and self.max_homophones != 1:
            raise ValueError("Monoalphabetic models require one homophone")
        if self.family != "verbose" and (self.min_code_length, self.max_code_length) != (1, 1):
            raise ValueError("Substitution models require length-one codes")


@dataclass
class Encoder:
    codebook: dict[str, tuple[Code, ...]]
    null_symbols: tuple[str, ...] = ()

    def __post_init__(self):
        if len(set(self.null_symbols)) != len(self.null_symbols) or any(
            not isinstance(s, str) or not s or any(c.isspace() for c in s) for s in self.null_symbols
        ):
            raise ValueError("Invalid null symbols")
        codes = [c for alternatives in self.codebook.values() for c in alternatives]
        if any(not alternatives for alternatives in self.codebook.values()) or any(not c for c in codes):
            raise ValueError("Empty code or homophone set")
        if any(g in self.null_symbols for code in codes for g in code):
            raise ValueError("Null glyphs cannot occur in codewords")
        for i, a in enumerate(codes):
            for b in codes[i + 1:]:
                if a[:len(b)] == b or b[:len(a)] == a:
                    raise ValueError("Codebook must be globally prefix-free")

    def encode(self, plaintext: Text, choices: tuple[int, ...],
               nulls: tuple[NullInsertion, ...] = ()) -> Text:
        if len(choices) != plaintext.size:
            raise ValueError("One homophone choice is required per plaintext token")
        iterator = iter(choices)
        locations = {}
        for insertion in nulls:
            if (type(insertion.word) is not int or type(insertion.position) is not int
                    or not 0 <= insertion.word < len(plaintext.words) or insertion.position < 0
                    or insertion.symbol not in self.null_symbols
                    or (insertion.word, insertion.position) in locations):
                raise ValueError("Invalid null insertion")
            locations[insertion.word, insertion.position] = insertion.symbol
        words = []
        for wi, word in enumerate(plaintext.words):
            out = []
            boundaries = {0}
            for symbol in word:
                choice = next(iterator)
                if not 0 <= choice < len(self.codebook[symbol]):
                    raise ValueError("Invalid homophone choice")
                out.extend(self.codebook[symbol][choice])
                boundaries.add(len(out))
            count = sum(w == wi for w, _ in locations)
            if any(w == wi and p >= len(out) + count for w, p in locations):
                raise ValueError("Null insertion is outside its word")
            observed, cursor = [], 0
            for position in range(len(out) + count):
                if (wi, position) in locations:
                    if cursor not in boundaries:
                        raise ValueError("Nulls must lie between complete codewords")
                    observed.append(locations[wi, position])
                else:
                    observed.append(out[cursor])
                    cursor += 1
            words.append(tuple(observed))
        return Text(tuple(words))

    def decode(self, ciphertext: Text) -> Text:
        lookup = {code: symbol for symbol, codes in self.codebook.items() for code in codes}
        words = []
        for word in ciphertext.words:
            out, pending = [], ()
            for token in word:
                if token in self.null_symbols:
                    continue
                pending += (token,)
                if pending in lookup:
                    out.append(lookup[pending])
                    pending = ()
            if pending:
                raise ValueError("Ciphertext ends with an undecodable code")
            words.append(tuple(out))
        return Text(tuple(words))


def generate_encoder(plain: Alphabet, cipher: Alphabet, bounds: Bounds, seed: int) -> Encoder:
    """Seeded prefix-tree expansion, producing mixed-length prefix-free codes."""
    rng = random.Random(seed)
    needed = len(plain.symbols) * bounds.max_homophones
    if len(cipher.symbols) == 1:
        if needed != 1:
            raise ValueError("Unary prefix-free alphabet has capacity one")
        leaves = [(cipher.symbols[0],) * bounds.min_code_length]
    else:
        leaves = [(s,) for s in cipher.symbols]
        while len(leaves) < needed or any(len(c) < bounds.min_code_length for c in leaves):
            short = [c for c in leaves if len(c) < bounds.min_code_length]
            candidates = short or [c for c in leaves if len(c) < bounds.max_code_length]
            if not candidates:
                raise ValueError("Insufficient prefix-free code capacity")
            leaf = rng.choice(candidates)
            leaves.remove(leaf)
            leaves.extend(leaf + (s,) for s in cipher.symbols)
        # Expand a few leaves to exercise variable lengths even with ample capacity.
        if bounds.family == "verbose":
            for _ in range(needed):
                candidates = [c for c in leaves if len(c) < bounds.max_code_length]
                if not candidates:
                    break
                leaf = rng.choice(candidates)
                leaves.remove(leaf)
                leaves.extend(leaf + (s,) for s in cipher.symbols)
    rng.shuffle(leaves)
    return Encoder({s: tuple(leaves[i * bounds.max_homophones:(i + 1) * bounds.max_homophones])
                    for i, s in enumerate(plain.symbols)})


def generate_ciphertext(plaintext: Text, encoder: Encoder, seed: int) -> tuple[Text, tuple[int, ...]]:
    rng = random.Random(seed)
    choices = tuple(rng.randrange(len(encoder.codebook[s])) for w in plaintext.words for s in w)
    return encoder.encode(plaintext, choices), choices
