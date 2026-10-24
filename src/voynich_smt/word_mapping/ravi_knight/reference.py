"""Small dense bigram HMM reference, using natural logarithms.

Source states are plaintext IDs; observations are cipher IDs. Channel rows are
P(cipher | plaintext). Sequences are nonempty observed segments. The source
model is a proper variable-length distribution: each state transitions either
to another plaintext state or EOS. BOS is represented by ``initial``.

This deliberately uses Python tuples and dense loops so later implementations
have a simple independent correctness oracle. It is not a large-corpus backend.
"""
from dataclasses import dataclass
import math


def _log(value):
    return math.log(value) if value else -math.inf


def _logsum(values):
    values = tuple(values)
    maximum = max(values, default=-math.inf)
    if maximum == -math.inf:
        return maximum
    return maximum + math.log(sum(math.exp(v - maximum) for v in values))


def _distribution(values):
    return (all(math.isfinite(x) and x >= 0 for x in values)
            and math.isclose(sum(values), 1.0, rel_tol=1e-10, abs_tol=1e-12))


@dataclass(frozen=True)
class BigramHMM:
    initial: tuple[float, ...]
    transition: tuple[tuple[float, ...], ...]
    final: tuple[float, ...]
    channel: tuple[tuple[float, ...], ...]

    def __post_init__(self):
        # Own immutable copies even when callers provide lists.
        for name in ('initial', 'final'):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        for name in ('transition', 'channel'):
            object.__setattr__(self, name, tuple(tuple(r) for r in getattr(self, name)))
        n = len(self.initial)
        if not n or len(self.transition) != n or len(self.final) != n or len(self.channel) != n:
            raise ValueError('Inconsistent source dimensions')
        width = len(self.channel[0])
        if not width or any(len(r) != width for r in self.channel):
            raise ValueError('Inconsistent channel dimensions')
        if not _distribution(self.initial):
            raise ValueError('Initial probabilities must normalize')
        for row, end in zip(self.transition, self.final):
            if len(row) != n or not _distribution((*row, end)):
                raise ValueError('Transitions including EOS must normalize')
        if not all(_distribution(row) for row in self.channel):
            raise ValueError('Channel rows must normalize over cipher IDs')

    def observations(self, sequence):
        sequence = tuple(sequence)
        if not sequence or any(type(x) is not int or not 0 <= x < len(self.channel[0])
                               for x in sequence):
            raise ValueError('Expected nonempty sequence of valid cipher IDs')
        return sequence

    def joint_log_probability(self, observations, states):
        observations = self.observations(observations)
        states = tuple(states)
        if len(states) != len(observations) or any(
                type(s) is not int or not 0 <= s < len(self.initial) for s in states):
            raise ValueError('Expected one valid plaintext ID per observation')
        score = _log(self.initial[states[0]]) + _log(self.final[states[-1]])
        score += sum(_log(self.channel[s][c]) for s, c in zip(states, observations))
        score += sum(_log(self.transition[a][b]) for a, b in zip(states, states[1:]))
        return score


@dataclass(frozen=True)
class Posterior:
    log_evidence: float
    marginals: tuple[tuple[float, ...], ...]
    expected_initial: tuple[float, ...]
    expected_transition: tuple[tuple[float, ...], ...]
    expected_final: tuple[float, ...]
    expected_channel: tuple[tuple[float, ...], ...]


def forward_backward(model, observations):
    """Exact conditional marginals/counts for one observed segment.

    Impossible evidence raises ValueError because its conditional is undefined.
    """
    obs = model.observations(observations)
    n, length = len(model.initial), len(obs)
    trans = tuple(tuple(_log(x) for x in row) for row in model.transition)
    emission = tuple(tuple(_log(model.channel[s][c]) for s in range(n)) for c in obs)
    alpha = [tuple(_log(model.initial[s]) + emission[0][s] for s in range(n))]
    for t in range(1, length):
        alpha.append(tuple(emission[t][b] + _logsum(
            alpha[-1][a] + trans[a][b] for a in range(n)) for b in range(n)))
    evidence = _logsum(alpha[-1][s] + _log(model.final[s]) for s in range(n))
    if evidence == -math.inf:
        raise ValueError('Observation sequence has zero probability')
    beta = [None] * length
    beta[-1] = tuple(_log(x) for x in model.final)
    for t in range(length - 2, -1, -1):
        beta[t] = tuple(_logsum(trans[a][b] + emission[t + 1][b] + beta[t + 1][b]
                                   for b in range(n)) for a in range(n))
    marginals = tuple(tuple(math.exp(alpha[t][s] + beta[t][s] - evidence)
                            for s in range(n)) for t in range(length))
    transitions = [[0.0] * n for _ in range(n)]
    channel = [[0.0] * len(model.channel[0]) for _ in range(n)]
    for t, c in enumerate(obs):
        for a in range(n):
            channel[a][c] += marginals[t][a]
            if t + 1 < length:
                for b in range(n):
                    transitions[a][b] += math.exp(alpha[t][a] + trans[a][b]
                        + emission[t + 1][b] + beta[t + 1][b] - evidence)
    return Posterior(evidence, marginals, marginals[0],
                     tuple(map(tuple, transitions)), marginals[-1], tuple(map(tuple, channel)))


def viterbi(model, observations, *, channel_exponent=1.0):
    """Return (plaintext IDs, log score); ties follow lowest predecessor ID.

    The published final-decoding exponent is 3; inference defaults to the
    ordinary joint probability. A stretched score is not normalized evidence.
    """
    obs = model.observations(observations)
    if not math.isfinite(channel_exponent) or channel_exponent <= 0:
        raise ValueError('Channel exponent must be finite and positive')
    n = len(model.initial)
    scores = tuple(_log(model.initial[s]) + channel_exponent * _log(model.channel[s][obs[0]])
                   for s in range(n))
    back = []
    for c in obs[1:]:
        predecessors = tuple(max(range(n), key=lambda a: scores[a] + _log(model.transition[a][b]))
                             for b in range(n))
        scores = tuple(scores[predecessors[b]] + _log(model.transition[predecessors[b]][b])
                       + channel_exponent * _log(model.channel[b][c]) for b in range(n))
        back.append(predecessors)
    last = max(range(n), key=lambda s: scores[s] + _log(model.final[s]))
    score = scores[last] + _log(model.final[last])
    if score == -math.inf:
        raise ValueError('Observation sequence has zero probability')
    path = [last]
    for predecessors in reversed(back):
        path.append(predecessors[path[-1]])
    return tuple(reversed(path)), score
