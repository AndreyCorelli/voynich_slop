"""Check probability attribution across observed, unseen and boundary events."""
import math
import pytest
from benchmarks.word_mapping_first_corruption import explain, events
from voynich_smt.word_mapping.ngram import BOS, EOS, NgramConfig, NgramModel


@pytest.mark.parametrize('weights', [(0, .5, .5), (.2, .3, .5), (1, 0, 0)])
def test_probability_paths_and_event_score(weights):
    model = NgramModel.train([('a', 'b', 'a'), ('b', 'c')], NgramConfig(
        unigram_weight=weights[0], bigram_weight=weights[1], trigram_weight=weights[2]))
    ids = [BOS, *model.form_ids.values()]
    for a in ids:
        for b in ids:
            for c in [EOS, 2, *model.form_ids.values()]:
                row = explain(model, (a, b, c))
                assert math.isclose(sum(row['probability_mass'].values()), model.probability(a, b, c), rel_tol=1e-12)
    segment = ('a', 'c', 'b')
    score = sum(explain(model, e)['log_score'] for e in events(model, segment))
    assert math.isclose(score, model.score([segment]).log_likelihood, abs_tol=1e-12)
