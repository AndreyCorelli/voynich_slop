from copy import deepcopy

from benchmarks.ravi_knight_restart_selection import summarize


def test_selection_uses_likelihood_not_truth_and_breaks_ties_by_seed():
    stage = {'types': 1, 'source': {}, 'cipher_vocabulary': ['x'],
             'log_likelihoods': [-3.], 'token_accuracy': .9}
    runs = [{'seed': 5, 'stages': [deepcopy(stage)]}, {'seed': 3, 'stages': [deepcopy(stage)]}]
    runs[1]['stages'][0]['token_accuracy'] = .1
    result = summarize({'runs': runs})
    assert result['selected']['seed'] == 3
    assert not result['selected_matches_best_recovery']
    runs[1]['stages'][0]['token_accuracy'] = 1.
    assert summarize({'runs': runs})['selected']['seed'] == 3
