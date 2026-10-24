from dataclasses import replace

import pytest

from voynich_smt.word_mapping.ravi_knight.em import fit_channel
from voynich_smt.word_mapping.ravi_knight.iterative import confident_pairs, fit_iterative
from voynich_smt.word_mapping.ravi_knight.reference import BigramHMM


def test_frozen_rows_preserve_direction_and_allow_collisions():
    model = BigramHMM((.5, .5), ((.4, .4), (.3, .3)), (.2, .4), ((.5, .5), (.6, .4)))
    result = fit_channel(model, [(0,), (0, 1)], frozen={0: 0}, max_iterations=10)
    assert result.model.channel[0] == (1., 0.)
    assert result.model.channel[1][0] > 0  # No reciprocal exclusion.
    assert all(b >= a - 1e-9 for a, b in zip(result.log_likelihoods, result.log_likelihoods[1:]))
    with pytest.raises(ValueError):
        fit_channel(model, [(0,)], frozen={2: 0})


def test_expansion_rebuilds_unknown_and_carries_confident_words():
    training = [('the', 'cat', 'runs')] * 20 + [('a', 'dog', 'walks')] * 5
    cipher = [('x', 'y', 'z')] * 20 + [('u', 'v', 'w')] * 5
    stages = fit_iterative(training, cipher, sizes=(2, 4, 6, 8), seed=4, max_iterations=20)
    assert len(stages) == 3  # Stop after vocabulary saturation.
    assert stages[0].source.vocabulary[0] == '<UNKNOWN>'
    assert stages[0].cipher_coverage < stages[-1].cipher_coverage == 1
    assert stages[-1].source_coverage == 1
    for previous, stage in zip(stages, stages[1:]):
        expected = dict(previous.frozen)
        expected.update(confident_pairs(previous))
        assert dict(stage.frozen) == expected
        for word, cipher_word in stage.frozen:
            s = stage.source.vocabulary.index(word)
            c = stage.cipher_vocabulary.index(cipher_word)
            assert stage.result.model.channel[s][c] == 1
    assert stages == fit_iterative(training, cipher, sizes=(2, 4, 6, 8), seed=4, max_iterations=20)
    assert len(stages[-1].decode(cipher)) == len(cipher)
    assert all(not s.frozen for s in fit_iterative(training, cipher, sizes=(2, 6), freeze=False, max_iterations=2))


def test_confidence_threshold_is_strict_and_unknown_is_not_frozen():
    stage = fit_iterative([('a', 'b')], [('x', 'y')], sizes=(2,), max_iterations=1)[0]
    model = replace(stage.result.model, channel=((0., .9, .1), (.9, .1, 0.), (0., .5, .5)))
    stage = replace(stage, result=replace(stage.result, model=model))
    assert confident_pairs(stage) == ()
    model = replace(model, channel=((0., .9, .1), (0., .8, .2), (0., .7, .3)))
    stage = replace(stage, result=replace(stage.result, model=model))
    assert len(confident_pairs(stage)) == 2  # Same cipher word allowed.


@pytest.mark.parametrize('sizes', [(), (0,), (2, 1), (2, 2), (True,)])
def test_invalid_schedule(sizes):
    with pytest.raises(ValueError):
        fit_iterative([('a',)], [('x',)], sizes=sizes)


def test_frequency_initializer_freezing_and_replay():
    training = [('the', 'cat', 'runs')] * 8 + [('a', 'dog', 'walks')] * 3
    cipher = [('x', 'y', 'z')] * 8 + [('u', 'v', 'w')] * 3
    options = dict(sizes=(2, 4, 6), initialization='frequency', seed=3, max_iterations=4)
    stages = fit_iterative(training, cipher, **options)
    assert stages == fit_iterative(training, cipher, **options)
    relaxed = fit_iterative(training, cipher, freeze=False, **options)
    assert stages[0] == relaxed[0]  # First stage is identical before any freezing.
    assert all(not stage.frozen for stage in relaxed)
    for stage in stages:
        for w, c in stage.frozen:
            assert stage.result.model.channel[stage.source.vocabulary.index(w)][stage.cipher_vocabulary.index(c)] == 1


def test_warm_transfer_splits_unknown_and_reopens_zero_probabilities():
    from voynich_smt.word_mapping.ravi_knight.iterative import transfer_channel
    previous = fit_iterative([('a', 'a', 'b')], [('x', 'x', 'y')], sizes=(1,), max_iterations=1)[0]
    model = replace(previous.result.model, channel=((.5, .5), (.4, .6)))
    previous = replace(previous, result=replace(previous.result, model=model))
    # Reorder IDs deliberately to check identity-based transfer.
    source = ('<UNKNOWN>', 'b', 'a')
    cipher = ('<UNKNOWN>', 'y', 'x')
    fresh = ((1/3, 1/3, 1/3),) * 3
    transferred = transfer_channel(previous, source, cipher,
                                   {'x': 8, 'y': 3, 'z': 1}, fresh, exploration=.1)
    assert transferred[0] == fresh[0]
    assert transferred[1] == fresh[1]
    assert transferred[2] == pytest.approx(tuple(.9 * p + .1/3 for p in (.1, .3, .6)))
    zero_model = replace(model, channel=((.5, .5), (0., 1.)))
    previous = replace(previous, result=replace(previous.result, model=zero_model))
    reopened = transfer_channel(previous, source, cipher, {'x': 8, 'y': 3}, fresh)
    assert all(min(row) > 0 and sum(row) == pytest.approx(1) for row in reopened)


def test_warm_start_is_revisable_deterministic_and_matches_first_stage():
    training = [('a', 'b', 'c')] * 4 + [('d', 'a')]
    cipher = [('x', 'y', 'z')] * 4 + [('w', 'x')]
    options = dict(sizes=(2, 4), max_iterations=3, freeze=False, seed=3)
    fresh = fit_iterative(training, cipher, **options)
    warm = fit_iterative(training, cipher, warm_start=True, **options)
    assert warm[0] == fresh[0]
    assert warm == fit_iterative(training, cipher, warm_start=True, **options)
    assert not any(s.frozen for s in warm)
    assert warm[-1].result.log_likelihoods[0] != fresh[-1].result.log_likelihoods[0]
    with pytest.raises(ValueError, match='freeze=False'):
        fit_iterative(training, cipher, warm_start=True)


def test_fixed_cipher_ranking_stays_fixed_when_counts_change():
    training = [('a', 'b', 'c')]
    cipher = [('x', 'y', 'z')] + [('z',)] * 10
    stages = fit_iterative(training, cipher, sizes=(1, 2), cipher_order=('x', 'y'), max_iterations=1)
    assert stages[-1].cipher_vocabulary == ('<UNKNOWN>', 'x', 'y')
    assert stages[-1].cipher_coverage == pytest.approx(2/13)
    with pytest.raises(ValueError):
        fit_iterative(training, cipher, sizes=(1,), cipher_order=('missing',))
