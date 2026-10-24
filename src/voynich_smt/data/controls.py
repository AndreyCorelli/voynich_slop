"""Seeded controls with explicit preserved properties and exact word lengths."""
from dataclasses import asdict
import random

from voynich_smt.models.text import Text
from .corpus import digest


def control(text, kind, seed):
    rng = random.Random(seed)
    words = [list(w) for w in text.words]
    if kind == 'word-shuffle':
        rng.shuffle(words)
    elif kind == 'within-word-shuffle':
        for word in words:
            rng.shuffle(word)
    elif kind in {'frequency-shuffle', 'uniform'}:
        flat = [g for w in words for g in w]
        if kind == 'frequency-shuffle':
            rng.shuffle(flat)
        else:
            alphabet = sorted(set(flat))
            flat = [rng.choice(alphabet) for _ in flat]
        position, new = 0, []
        for word in words:
            new.append(flat[position:position + len(word)])
            position += len(word)
        words = new
    elif kind == 'prefix-stem-suffix':
        # A measured-shape pseudo-language: sampled source prefixes/suffixes,
        # independent uniform stems, source word lengths, no Latin constraint.
        alphabet = sorted({g for w in words for g in w})
        first = [w[0] for w in words]
        last = [w[-1] for w in words]
        words = [[rng.choice(first)] + [rng.choice(alphabet) for _ in range(len(w) - 2)]
                 + [rng.choice(last)] if len(w) >= 2 else [rng.choice(first)] for w in words]
    else:
        raise ValueError('Unknown control kind')
    result = Text(tuple(tuple(w) for w in words))
    return result, {'kind': kind, 'seed': seed, 'generator_version': 1,
                    'source_text_sha256': digest(asdict(text)), 'text': asdict(result)}
