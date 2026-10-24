import pytest
from benchmarks.word_mapping_diverse_candidates import diverse_select


def test_distance_retains_other_basin_before_nearby_high_scores():
    rows = [
        {'score': 10, 'assignments': {'a': 0, 'b': 1, 'c': 2}},
        {'score': 9, 'assignments': {'a': 0, 'b': 1, 'c': 3}},
        {'score': 8, 'assignments': {'a': 4, 'b': 5, 'c': 6}},
        {'score': 7, 'assignments': {'a': 4, 'b': 5, 'c': 6}},
    ]
    assert diverse_select(rows, 2) == [rows[0], rows[2]]
    assert len(diverse_select(rows, 10)) == 3
    assert diverse_select(list(reversed(rows)), 2) == [rows[0], rows[2]]


def test_diversity_rejects_incompatible_domains_and_invalid_budget():
    with pytest.raises(ValueError, match='domains differ'):
        diverse_select([{'score': 1, 'assignments': {'a': 0}}, {'score': 0, 'assignments': {'b': 1}}], 2)
    with pytest.raises(ValueError, match='Positive'):
        diverse_select([], True)
    with pytest.raises(ValueError, match='Empty'):
        diverse_select([], 2)
