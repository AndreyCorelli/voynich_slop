"""Training-only restricted vocabulary and additive-smoothed bigram source."""
from collections import Counter
from dataclasses import dataclass
import math

from .reference import BigramHMM

UNKNOWN = '<UNKNOWN>'


def _segments(segments):
    segments = tuple(tuple(s) for s in segments)
    if not segments or any(not s for s in segments):
        raise ValueError('Expected nonempty segments')
    if any(not isinstance(w, str) or not w or w == UNKNOWN or any(c.isspace() for c in w)
           for s in segments for w in s):
        raise ValueError('Expected surface words, without reserved UNKNOWN')
    return segments


@dataclass(frozen=True)
class SourceModel:
    vocabulary: tuple[str, ...]  # UNKNOWN is always ID zero.
    counts: tuple[int, ...]
    initial: tuple[float, ...]
    transition: tuple[tuple[float, ...], ...]
    final: tuple[float, ...]

    def encode(self, segments):
        ids = {w: i for i, w in enumerate(self.vocabulary)}
        return tuple(tuple(ids.get(w, 0) for w in s) for s in _segments(segments))

    def hmm(self, channel):
        return BigramHMM(self.initial, self.transition, self.final, channel)


def train_bigram(segments, *, max_types=None, smoothing=0.1):
    """Rank only independent training words, then collapse excluded words.

    Smoothing is a per-outcome pseudocount. UNKNOWN participates in contexts;
    it is neither a barrier nor a reason to omit a token from the likelihood.
    Sentence boundaries are supplied by the caller and never inferred here.
    """
    segments = _segments(segments)
    if max_types is not None and (type(max_types) is not int or max_types < 1):
        raise ValueError('max_types must be a positive integer or None')
    if not math.isfinite(smoothing) or smoothing <= 0:
        raise ValueError('smoothing must be finite and positive')
    frequencies = Counter(w for s in segments for w in s)
    ranked = sorted(frequencies, key=lambda w: (-frequencies[w], w))
    vocabulary = (UNKNOWN, *ranked[:max_types])
    ids = {w: i for i, w in enumerate(vocabulary)}
    n = len(vocabulary)
    initial = [smoothing] * n
    transitions = [[smoothing] * n for _ in range(n)]
    final = [smoothing] * n
    counts = [0] * n
    for segment in segments:
        states = tuple(ids.get(w, 0) for w in segment)
        initial[states[0]] += 1
        final[states[-1]] += 1
        for s in states:
            counts[s] += 1
        for a, b in zip(states, states[1:]):
            transitions[a][b] += 1
    initial_total = sum(initial)
    totals = [sum(row) + end for row, end in zip(transitions, final)]
    return SourceModel(vocabulary, tuple(counts), tuple(x / initial_total for x in initial),
                       tuple(tuple(x / total for x in row) for row, total in zip(transitions, totals)),
                       tuple(x / total for x, total in zip(final, totals)))
