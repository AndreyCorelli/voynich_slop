"""Explicit bounds and complexity conventions for extended experiments."""

from dataclasses import dataclass, field


def nonnegative_integer(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


@dataclass(frozen=True)
class HomophoneSelection:
    """Free occurrence choices, or a separate zero-start cycle for each letter."""

    mode: str = "free"
    reset: str = "text"

    def __post_init__(self):
        if (not isinstance(self.mode, str) or not isinstance(self.reset, str)
                or self.mode not in {"free", "cycle"} or self.reset not in {"text", "word"}):
            raise ValueError("Invalid homophone selection policy")
        if self.mode == "free" and self.reset != "text":
            raise ValueError("Free selection has no reset policy")


@dataclass(frozen=True)
class NullBounds:
    enabled: bool = False
    max_distinct_symbols: int = 0
    max_occurrences: int = 0
    max_consecutive: int = 0

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be Boolean")
        for name in ("max_distinct_symbols", "max_occurrences", "max_consecutive"):
            nonnegative_integer(getattr(self, name), name)
        if not self.enabled and any((self.max_distinct_symbols, self.max_occurrences, self.max_consecutive)):
            raise ValueError("Disabled nulls require zero budgets")


@dataclass(frozen=True)
class ComplexityWeights:
    mappings: int = 1
    additional_homophones: int = 1
    extra_code_glyphs: int = 1
    distinct_null_symbols: int = 2
    null_occurrences: int = 1

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            nonnegative_integer(getattr(self, name), name)


@dataclass(frozen=True)
class Optimization:
    enabled: bool = False
    method: str = "lexicographic"
    weights: ComplexityWeights = field(default_factory=ComplexityWeights)

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be Boolean")
        if not isinstance(self.method, str) or self.method not in {"lexicographic", "weighted"}:
            raise ValueError("Unknown optimization method")
        if not isinstance(self.weights, ComplexityWeights):
            raise ValueError("Invalid complexity weights")
