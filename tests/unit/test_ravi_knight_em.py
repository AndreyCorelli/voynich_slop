from itertools import product
import math

import pytest

from voynich_smt.word_mapping.ravi_knight.em import expectation, fit_channel, random_channel
from voynich_smt.word_mapping.ravi_knight.lm import UNKNOWN, train_bigram
from voynich_smt.word_mapping.ravi_knight.reference import BigramHMM


def test_restricted_training_counts_boundaries_and_unknown_contexts():
    source = train_bigram([['a', 'rare', 'a'], ['a', 'other']], max_types=1, smoothing=1)
    assert source.vocabulary == (UNKNOWN, 'a')
    assert source.counts == (2, 3)
    assert source.initial == pytest.approx((1 / 4, 3 / 4))
    assert source.transition[0] == pytest.approx((1 / 5, 2 / 5))
    assert source.final[0] == pytest.approx(2 / 5)
    assert source.transition[1] == pytest.approx((3 / 6, 1 / 6))
    assert source.final[1] == pytest.approx(2 / 6)
    assert source.encode([['new', 'a']]) == ((0, 1),)
    assert train_bigram([['b', 'a']]).vocabulary == (UNKNOWN, 'a', 'b')


def test_single_em_step_matches_enumerated_corpus_counts():
    model = BigramHMM((.6, .4), ((.5, .3), (.2, .5)), (.2, .3), ((.7, .3), (.2, .8)))
    segments = ((0, 1, 0), (1,))
    counts = [[0., 0.], [0., 0.]]
    evidence = 0.
    for obs in segments:
        paths = list(product(range(2), repeat=len(obs)))
        weights = [math.exp(model.joint_log_probability(obs, p)) for p in paths]
        total = sum(weights)
        evidence += math.log(total)
        for path, weight in zip(paths, weights):
            for s, c in zip(path, obs):
                counts[s][c] += weight / total
    ll, actual = expectation(model, segments)
    assert ll == pytest.approx(evidence)
    result = fit_channel(model, segments, max_iterations=1)
    for s in range(2):
        assert actual[s] == pytest.approx(counts[s])
        assert result.model.channel[s] == pytest.approx([x / sum(counts[s]) for x in counts[s]])
    assert result.model.initial == model.initial
    assert result.model.transition == model.transition
    assert result.model.final == model.final


def test_em_monotonic_reproducible_and_normalized():
    source = train_bigram([['the', 'cat', 'runs'], ['a', 'dog', 'walks']] * 5)
    channel = random_channel(len(source.vocabulary), 3, seed=42)
    model = source.hmm(channel)
    segments = ((0, 1, 2), (0, 1), (2, 0, 1))
    result = fit_channel(model, segments, max_iterations=30)
    assert all(b >= a - 1e-9 for a, b in zip(result.log_likelihoods, result.log_likelihoods[1:]))
    assert all(sum(row) == pytest.approx(1) for row in result.model.channel)
    assert fit_channel(model, iter(segments), max_iterations=30) == result
    assert random_channel(len(source.vocabulary), 3, seed=42) == channel


def test_unoccupied_row_is_preserved():
    model = BigramHMM((1., 0.), ((.5, 0.), (0., .5)), (.5, .5), ((.5, .5), (.3, .7)))
    result = fit_channel(model, [(0,), (0,)])
    assert result.converged
    assert result.model.channel == ((1., 0.), (.3, .7))


@pytest.mark.parametrize('segments, kwargs', [([], {}), ([[]], {}), ([[UNKNOWN]], {}),
    ([['x']], {'max_types': 0}), ([['x']], {'smoothing': 0}), ([['x']], {'smoothing': float('nan')})])
def test_bad_training_inputs(segments, kwargs):
    with pytest.raises(ValueError):
        train_bigram(segments, **kwargs)


def test_frequency_initialization_has_full_support_and_correct_direction():
    from voynich_smt.word_mapping.ravi_knight.em import frequency_channel
    base = random_channel(4, 3, seed=7)
    channel = frequency_channel(4, 3, seed=7, strength=.5)
    assert channel[0] == base[0]  # UNKNOWN is not frequency-matched.
    assert channel[3] == base[3]  # Unmatched real source row remains random.
    for s in (1, 2):
        assert channel[s][s] == pytest.approx(.5 + .5 * base[s][s])
        assert max(range(3), key=lambda c: channel[s][c]) == s
    assert all(sum(row) == pytest.approx(1) and min(row) > 0 for row in channel)
    assert frequency_channel(4, 3, seed=7, strength=0) == base
    with pytest.raises(ValueError):
        frequency_channel(4, 3, seed=7, strength=1)
