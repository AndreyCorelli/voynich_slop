from dataclasses import dataclass


@dataclass(frozen=True)
class Alphabet:
    """Ordered atomic symbols; spaces are never alphabet members."""

    symbols: tuple[str, ...]

    def __post_init__(self):
        if not self.symbols or len(set(self.symbols)) != len(self.symbols):
            raise ValueError("Alphabet must be nonempty and unique")
        if any(not s or any(c.isspace() for c in s) for s in self.symbols):
            raise ValueError("Symbols must be nonempty and contain no whitespace")

    def index(self, symbol: str) -> int:
        return self.symbols.index(symbol)
