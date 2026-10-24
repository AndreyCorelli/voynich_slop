from dataclasses import dataclass, field

from voynich_smt.cipher.base import Bounds
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.models.settings import NullBounds, Optimization, ComplexityWeights, HomophoneSelection
from voynich_smt.solver.recovery import Recovery, recover_dictionary


@dataclass(frozen=True)
class HiddenRecoveryRequest:
    """Solver input contract deliberately excludes all hidden ground truth."""

    ciphertext: Text
    plaintext_alphabet: Alphabet
    ciphertext_alphabet: Alphabet
    bounds: Bounds
    dictionary: WordDictionary
    timeout_ms: int = 10_000
    min_word_length: int = 1
    max_word_length: int | None = None
    representation: str = "finite"
    nulls: NullBounds = field(default_factory=NullBounds)
    optimization: Optimization = field(default_factory=Optimization)
    selection: HomophoneSelection = field(default_factory=HomophoneSelection)
    dictionary_encoding: str = "flat"

    def __post_init__(self):
        if type(self.timeout_ms) is not int or self.timeout_ms <= 0:
            raise ValueError("Timeout must be a positive integer")
        if type(self.min_word_length) is not int or self.min_word_length < 1:
            raise ValueError("Invalid minimum word length")
        if self.max_word_length is not None and (
            type(self.max_word_length) is not int or self.max_word_length < self.min_word_length
        ):
            raise ValueError("Invalid maximum word length")
        if self.representation not in {"finite", "ite", "array", "interval", "chunk"}:
            raise ValueError("Unknown representation")
        if self.dictionary_encoding not in {"flat", "trie", "entry"}:
            raise ValueError("Unknown dictionary encoding")
        if self.dictionary_encoding != "flat" and (self.nulls.enabled or self.optimization.enabled):
            raise ValueError("Non-flat dictionary encoding requires null-free feasibility")
        if (self.nulls.enabled or self.optimization.enabled) and self.representation != "finite":
            raise ValueError("Nulls and optimization require finite representation")
        self.ciphertext.validate(self.ciphertext_alphabet)
        self.dictionary.validate(self.plaintext_alphabet)

    def solve(self) -> Recovery:
        return recover_dictionary(self.ciphertext, self.plaintext_alphabet,
                                  self.ciphertext_alphabet, self.bounds, self.dictionary,
                                  self.timeout_ms, self.min_word_length, self.max_word_length,
                                  self.representation, self.nulls, self.optimization, self.selection,
                                  self.dictionary_encoding)

    @classmethod
    def from_dict(cls, data: dict) -> "HiddenRecoveryRequest":
        required = {"ciphertext", "plaintext_alphabet", "ciphertext_alphabet", "bounds", "dictionary"}
        optional = {"timeout_ms", "min_word_length", "max_word_length", "representation", "nulls", "optimization", "selection", "dictionary_encoding"}
        if not isinstance(data, dict) or not required <= data.keys() or data.keys() - required - optional:
            raise ValueError("Invalid request fields; hidden ground truth is not accepted")
        def settings(kind, value):
            if not isinstance(value, dict) or value.keys() - kind.__dataclass_fields__.keys():
                raise ValueError(f"Invalid {kind.__name__} fields")
            return kind(**value)

        nulls = settings(NullBounds, data.get("nulls", {}))
        selection = settings(HomophoneSelection, data.get("selection", {}))
        opt_data = data.get("optimization", {})
        if not isinstance(opt_data, dict):
            raise ValueError("Optimization settings must be an object")
        opt = dict(opt_data)
        weights = settings(ComplexityWeights, opt.pop("weights", {}))
        optimization = settings(Optimization, {**opt, "weights": weights})
        raw_bounds = data["bounds"]
        if (not isinstance(raw_bounds, dict) or set(raw_bounds) != set(Bounds.__dataclass_fields__)
                or not isinstance(raw_bounds["family"], str)
                or any(type(raw_bounds[k]) is not int for k in ("max_homophones", "min_code_length", "max_code_length"))):
            raise ValueError("Invalid cipher bounds")

        def tokens(value, field, words=False):
            key = "words" if words else "symbols"
            if not isinstance(value, dict) or set(value) != {key} or not isinstance(value[key], (list, tuple)):
                raise ValueError(f"Invalid {field} structure")
            sequence = value[key]
            if words:
                if any(not isinstance(w, (list, tuple)) or any(not isinstance(s, str) for s in w) for w in sequence):
                    raise ValueError(f"{field} requires arrays of tokenized words")
                return tuple(tuple(w) for w in sequence)
            if any(not isinstance(s, str) for s in sequence):
                raise ValueError(f"{field} requires string symbols")
            return tuple(sequence)

        return cls(Text(tokens(data["ciphertext"], "ciphertext", True)),
                   Alphabet(tokens(data["plaintext_alphabet"], "plaintext alphabet")),
                   Alphabet(tokens(data["ciphertext_alphabet"], "ciphertext alphabet")),
                   Bounds(**raw_bounds),
                   WordDictionary(tokens(data["dictionary"], "dictionary", True)),
                   **{k: data[k] for k in optional - {"nulls", "optimization", "selection"} if k in data},
                   nulls=nulls, optimization=optimization, selection=selection)
