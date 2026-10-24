"""Fixed-vocabulary maximum-likelihood channel EM with a frozen source LM."""
from dataclasses import dataclass
import math
import random

from .reference import BigramHMM, forward_backward


@dataclass(frozen=True)
class EMResult:
    model: BigramHMM
    log_likelihoods: tuple[float, ...]  # Initial value followed by each M-step.
    converged: bool


def random_channel(source_types, cipher_types, *, seed):
    if any(type(n) is not int or n < 1 for n in (source_types, cipher_types)):
        raise ValueError('Vocabulary dimensions must be positive integers')
    rng = random.Random(seed)
    rows = []
    for _ in range(source_types):
        row = [0.5 + rng.random() for _ in range(cipher_types)]
        total = sum(row)
        rows.append(tuple(x / total for x in row))
    return tuple(rows)


def expectation(model, segments):
    """Return corpus log evidence and summed channel sufficient statistics."""
    segments = tuple(tuple(s) for s in segments)
    if not segments:
        raise ValueError('Expected at least one observed segment')
    counts = [[0.] * len(model.channel[0]) for _ in model.initial]
    likelihoods = []
    for segment in segments:
        posterior = forward_backward(model, segment)
        likelihoods.append(posterior.log_evidence)
        for target, row in zip(counts, posterior.expected_channel):
            for c, value in enumerate(row):
                target[c] += value
    return math.fsum(likelihoods), tuple(map(tuple, counts))


def fit_channel(model, segments, *, max_iterations=100, tolerance=1e-7, frozen=None):
    """Exact EM, optionally fixing specified source rows to single cipher IDs.

    Tolerance is absolute corpus log-likelihood improvement per update. Preserve
    an unoccupied row because the likelihood does not constrain that row.
    """
    if type(max_iterations) is not int or max_iterations < 1:
        raise ValueError('max_iterations must be positive')
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('tolerance must be finite and nonnegative')
    frozen = dict(frozen or {})
    n, width = len(model.initial), len(model.channel[0])
    if any(type(s) is not int or type(c) is not int or not 0 <= s < n
           or not 0 <= c < width for s, c in frozen.items()):
        raise ValueError('Invalid frozen row assignment')
    if frozen:
        channel = tuple(tuple(float(c == frozen[s]) for c in range(width))
                        if s in frozen else row for s, row in enumerate(model.channel))
        model = BigramHMM(model.initial, model.transition, model.final, channel)
    segments = tuple(tuple(s) for s in segments)
    likelihood, counts = expectation(model, segments)
    history = [likelihood]
    converged = False
    for _ in range(max_iterations):
        channel = tuple(tuple(x / sum(row) for x in row) if sum(row) else old
                        for row, old in zip(counts, model.channel))
        channel = tuple(model.channel[s] if s in frozen else row
                        for s, row in enumerate(channel))
        updated = BigramHMM(model.initial, model.transition, model.final, channel)
        likelihood, counts = expectation(updated, segments)
        improvement = likelihood - history[-1]
        if improvement < -1e-8 * max(1., abs(history[-1])):
            raise ArithmeticError('EM likelihood decreased beyond numerical tolerance')
        history.append(likelihood)
        model = updated
        if abs(improvement) <= tolerance:
            converged = True
            break
    return EMResult(model, tuple(history), converged)


def frequency_channel(source_types, cipher_types, *, seed, strength=0.5):
    """Mix positive random rows with equal-rank real-word assignments.

    IDs must be frequency-ranked with UNKNOWN at zero. No truth or matched
    vocabulary is supplied. UNKNOWN and unmatched source rows retain the random
    distribution. The random component gives every destination positive mass.
    This is a reference dense initializer, not a full-inventory allocation API.
    """
    if not math.isfinite(strength) or not 0 <= strength < 1:
        raise ValueError('strength must be finite and in [0, 1)')
    base = random_channel(source_types, cipher_types, seed=seed)
    return tuple(tuple((1 - strength) * value + strength * float(c == s)
                       for c, value in enumerate(row))
                 if 0 < s < cipher_types else row for s, row in enumerate(base))
