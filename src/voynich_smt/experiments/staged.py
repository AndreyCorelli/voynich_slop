"""Validated workload specifications for staged hidden-plaintext validation."""

from dataclasses import dataclass
import re

from voynich_smt.cipher.base import Bounds
from voynich_smt.experiments.fixtures import LATIN
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet

REPRESENTATIONS = {"ite", "array", "interval", "chunk", "finite"}


@dataclass(frozen=True)
class Stage:
    name: str
    dictionary: WordDictionary
    ciphertext_alphabet: Alphabet
    bounds: Bounds


@dataclass(frozen=True)
class StagedConfig:
    plaintext_alphabet: Alphabet
    seeds: tuple[int, ...]
    sizes: tuple[int, ...]
    timeout_ms: int
    representation: str
    stages: tuple[Stage, ...]

    @classmethod
    def from_dict(cls, data: dict) -> "StagedConfig":
        required = {"plaintext_alphabet", "seeds", "sizes", "timeout_ms", "representation", "stages"}
        if not isinstance(data, dict) or data.keys() != required:
            raise ValueError("Invalid staged configuration fields")
        def alphabet(values):
            if not isinstance(values, list) or any(not isinstance(s, str) for s in values):
                raise ValueError("Alphabets must be lists of strings")
            return Alphabet(tuple(values))

        pa = alphabet(data["plaintext_alphabet"])
        for field in ("seeds", "sizes"):
            values = data[field]
            if (not isinstance(values, list) or not values or any(type(v) is not int for v in values)
                    or len(set(values)) != len(values)):
                raise ValueError(f"{field} must contain unique integers")
        if any(v <= 0 for v in data["sizes"]):
            raise ValueError("Sample sizes must be positive")
        if type(data["timeout_ms"]) is not int or data["timeout_ms"] <= 0:
            raise ValueError("Timeout must be a positive integer")
        if not isinstance(data["representation"], str) or data["representation"] not in REPRESENTATIONS:
            raise ValueError("Unknown representation")
        if not isinstance(data["stages"], list) or not data["stages"]:
            raise ValueError("At least one stage is required")
        stages = []
        for definition in data["stages"]:
            if not isinstance(definition, dict) or definition.keys() != {
                "name", "vocabulary_size", "ciphertext_alphabet", "bounds"
            }:
                raise ValueError("Invalid stage fields")
            name = definition["name"]
            if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
                raise ValueError("Stage names must be filename-safe identifiers")
            size = definition["vocabulary_size"]
            if type(size) is not int or not 1 <= size <= len(LATIN):
                raise ValueError("Invalid fixture vocabulary size")
            dictionary = WordDictionary.from_strings(LATIN[:size])
            dictionary.validate(pa)
            ca = alphabet(definition["ciphertext_alphabet"])
            fields = {"family", "max_homophones", "min_code_length", "max_code_length"}
            raw_bounds = definition["bounds"]
            if (not isinstance(raw_bounds, dict) or raw_bounds.keys() != fields
                    or not isinstance(raw_bounds["family"], str)
                    or any(type(raw_bounds[f]) is not int for f in fields - {"family"})):
                raise ValueError("Invalid cipher bounds")
            bounds = Bounds(**raw_bounds)
            if len(ca.symbols) ** bounds.max_code_length < len(pa.symbols) * bounds.max_homophones:
                raise ValueError("Stage cannot generate the requested prefix-free codebook")
            if any(s.name == name for s in stages):
                raise ValueError("Stage names must be unique")
            stages.append(Stage(name, dictionary, ca, bounds))
        return cls(pa, tuple(data["seeds"]), tuple(data["sizes"]), data["timeout_ms"],
                   data["representation"], tuple(stages))
