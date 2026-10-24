"""Versioned numerical and surface contracts for the first sparse reference."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ModelConfig:
    discount: float = 0.5
    unseen_mass: float = 0.01
    format_version: int = 1
    language: str = 'en'
    tokenization: str = 'english-continuous-v1'

    def __post_init__(self):
        if self.format_version != 1 or (self.language, self.tokenization) not in {
                ('en', 'english-continuous-v1'), ('la', 'latin-iu-continuous-v1'),
                ('de', 'ref-historical-continuous-v1')}:
            raise ValueError('Unsupported model contract')
        if not math.isfinite(self.discount) or not 0 < self.discount < 1:
            raise ValueError('discount must be strictly between zero and one')
        if not math.isfinite(self.unseen_mass) or not 0 < self.unseen_mass < 1:
            raise ValueError('unseen_mass must be strictly between zero and one')
