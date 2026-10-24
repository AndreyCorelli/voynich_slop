"""Enumeration is independent of the dynamic-programming implementation."""
from itertools import product
import math

import pytest

from voynich_smt.word_mapping.ravi_knight.reference import BigramHMM, forward_backward, viterbi


def model():
    return BigramHMM((.6, .4), ((.5, .3), (.2, .5)), (.2, .3),
                     ((.7, .2, .1), (.1, .3, .6)))


@pytest.mark.parametrize('obs', [(0,), (0, 2), (1, 0, 2, 0), (2, 2, 2)])
def test_posterior_and_viterbi_match_enumeration(obs):
    hmm = model()
    weighted = []
    for path in product(range(2), repeat=len(obs)):
        # Compute directly in probability space, without calling the joint scorer.
        p = hmm.initial[path[0]] * hmm.final[path[-1]]
        for s, c in zip(path, obs):
            p *= hmm.channel[s][c]
        for a, b in zip(path, path[1:]):
            p *= hmm.transition[a][b]
        weighted.append((path, p))
        assert hmm.joint_log_probability(obs, path) == pytest.approx(math.log(p))
    total = sum(p for _, p in weighted)
    posterior = forward_backward(hmm, obs)
    assert posterior.log_evidence == pytest.approx(math.log(total))
    for t in range(len(obs)):
        for s in range(2):
            expected = sum(p for path, p in weighted if path[t] == s) / total
            assert posterior.marginals[t][s] == pytest.approx(expected)
    for a in range(2):
        assert posterior.expected_initial[a] == pytest.approx(
            sum(p for path, p in weighted if path[0] == a) / total)
        assert posterior.expected_final[a] == pytest.approx(
            sum(p for path, p in weighted if path[-1] == a) / total)
        for b in range(2):
            expected = sum(p * sum(x == a and y == b for x, y in zip(path, path[1:]))
                           for path, p in weighted) / total
            assert posterior.expected_transition[a][b] == pytest.approx(expected)
        for c in range(3):
            expected = sum(p * sum(s == a and x == c for s, x in zip(path, obs))
                           for path, p in weighted) / total
            assert posterior.expected_channel[a][c] == pytest.approx(expected)
    best_path, best_p = max(weighted, key=lambda item: item[1])
    assert viterbi(hmm, obs) == (best_path, pytest.approx(math.log(best_p)))
    path, score = viterbi(hmm, obs, channel_exponent=3)
    def stretched(states):
        return hmm.joint_log_probability(obs, states) + 2 * sum(
            math.log(hmm.channel[s][c]) for s, c in zip(states, obs))
    assert score == pytest.approx(max(stretched(p) for p, _ in weighted))
    assert score == pytest.approx(stretched(path))


def test_log_space_survives_underflow():
    hmm = BigramHMM((1.,), ((.5,),), (.5,), ((1e-10, 1 - 1e-10),))
    result = forward_backward(hmm, [0] * 100)
    assert math.isfinite(result.log_evidence)
    assert result.expected_channel[0][0] == pytest.approx(100)
    assert result.expected_transition[0][0] == pytest.approx(99)


def test_zero_paths_and_ties():
    hmm = BigramHMM((.5, .5), ((.5, 0.), (0., .5)), (.5, .5), ((1., 0.), (1., 0.)))
    assert viterbi(hmm, [0, 0])[0] == (0, 0)
    assert forward_backward(hmm, [0]).marginals[0] == pytest.approx((.5, .5))
    for infer in (forward_backward, viterbi):
        with pytest.raises(ValueError, match='zero probability'):
            infer(hmm, [1])


@pytest.mark.parametrize('obs', [[], [-1], [3], [True], [0.5]])
def test_invalid_observations(obs):
    for infer in (forward_backward, viterbi):
        with pytest.raises(ValueError):
            infer(model(), obs)


def test_model_validation_and_ownership():
    with pytest.raises(ValueError):
        BigramHMM((1.,), ((1.,),), (.5,), ((1.,),))
    with pytest.raises(ValueError):
        BigramHMM((1.,), ((.5,),), (.5,), ((float('nan'),),))
    channel = [[1.]]
    hmm = BigramHMM([1.], [[.5]], [.5], channel)
    channel[0][0] = 0.
    assert hmm.channel == ((1.,),)
