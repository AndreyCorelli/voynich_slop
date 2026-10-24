"""The reranker must choose solely by its declared metric."""
import pytest
from benchmarks.word_mapping_neural_rerank import choose, freeze


def test_selection_uses_word_normalization_and_stable_ties():
    scores = [
        {'word_normalized_log_sum': -20, 'word_masked_log_sum': -20},
        {'word_normalized_log_sum': -10, 'word_masked_log_sum': -100},
        {'word_normalized_log_sum': -10, 'word_masked_log_sum': -15},
    ]
    assert choose(scores) == 1


@pytest.mark.parametrize('top', [0, 31, True, 1.5])
def test_budget_rejects_unbounded_or_invalid_selection(tmp_path, top):
    with pytest.raises(ValueError, match='top must'):
        freeze(tmp_path, top)
