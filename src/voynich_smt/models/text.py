from dataclasses import dataclass

from .alphabet import Alphabet


@dataclass(frozen=True)
class Text:
    """Atomic tokens grouped into nonempty words; boundaries are separate."""

    words: tuple[tuple[str, ...], ...]

    def __post_init__(self):
        if any(not w for w in self.words):
            raise ValueError("Words must be nonempty")
        if any(not s or any(c.isspace() for c in s) for w in self.words for s in w):
            raise ValueError("Invalid token")

    @classmethod
    def from_string(cls, text: str) -> "Text":
        """Convenience parser for single-character alphabets only."""
        return cls(tuple(tuple(w) for w in text.split()))

    def validate(self, alphabet: Alphabet) -> None:
        if any(s not in alphabet.symbols for w in self.words for s in w):
            raise ValueError("Text contains a symbol outside its alphabet")

    @property
    def size(self) -> int:
        return sum(map(len, self.words))
