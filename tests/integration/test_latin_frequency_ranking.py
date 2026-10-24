import math

from benchmarks.latin_frequency_ranking import frequency_score, rank_training


def test_counts_variants_as_expanded_words_and_keeps_unknowns():
    model = {'counts': {'et': 9, 'est': 1}, 'tokens': 10, 'alpha': 1}
    assert frequency_score(['et', 'et', 'est'], model) == frequency_score(['est', 'et', 'et'], model)
    assert frequency_score(['et', 'unseen'], model) < frequency_score(['et'], model)
    assert math.isclose(frequency_score(['unseen'], model), math.log(1/13))


def test_training_selection_ignores_truth_and_holdout_and_keeps_ties():
    model = {'counts': {'et': 9, 'est': 1}, 'tokens': 10, 'alpha': 1}
    candidates = [{'plaintext': {'words': ['est']}, 'truth': True},
                  {'plaintext': {'words': ['et']}, 'holdout': ['unseen']},
                  {'plaintext': {'words': ['et']}, 'truth': False}]
    values, order = rank_training(candidates, model)
    assert order == [1, 2, 0]
    candidates[0]['truth'] = False
    candidates[1]['holdout'] = ['et'] * 100
    assert rank_training(candidates, model) == (values, order)
