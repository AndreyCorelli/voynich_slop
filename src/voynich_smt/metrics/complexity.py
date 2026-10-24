"""Raw structural measurements and explicitly conventional integer scores."""

from voynich_smt.cipher.base import Encoder, NullInsertion
from voynich_smt.models.settings import ComplexityWeights


def measurements(encoder: Encoder, nulls: tuple[NullInsertion, ...] = ()) -> dict:
    codes = [c for alternatives in encoder.codebook.values() for c in alternatives]
    return {
        "mappings": len(codes),
        "additional_homophones": len(codes) - len(encoder.codebook),
        "total_codebook_glyphs": sum(map(len, codes)),
        "extra_code_glyphs": sum(len(c) - 1 for c in codes),
        "distinct_null_symbols": len(encoder.null_symbols),
        "null_occurrences": len(nulls),
        "code_lengths": [len(c) for c in codes],
        "context_rules": 0,
        "exceptions": 0,
    }


def weighted_score(raw: dict, weights: ComplexityWeights) -> int:
    return sum(raw[name] * getattr(weights, name) for name in weights.__dataclass_fields__)
