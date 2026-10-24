import pytest
from benchmarks.word_length_plausibility import windows, quantile


def records(*lengths):
    return [{'tokens':['a']*n} for n in lengths]


def test_passages_do_not_bridge_excluded_records():
    rows=list(windows(records(1,2,0,3,4,5),2,[5,5],1,3))
    assert [(r['start_record'],r['end_record_exclusive']) for r in rows]==[(0,2),(3,5),(4,6)]
    assert [r['lengths'] for r in rows]==[[1,2],[3,4],[4,5]]


def test_total_length_compatibility_does_not_imply_positionwise_compatibility():
    row=next(windows(records(2,6),2,[4,5],1,3))
    assert 3<=row['total_letters']<=9
    assert not row['positionwise_length_compatible']
    compatible=next(windows(records(2,2),2,[4,5],1,3))
    assert compatible['positionwise_length_compatible']


def test_lower_code_length_bound_also_restricts_passages():
    row=next(windows(records(3),1,[5],2,3))
    assert not row['positionwise_length_compatible']


def test_distribution_quantiles_include_endpoints_and_even_median():
    assert quantile([7,1,5,3],0)==1
    assert quantile([7,1,5,3],.5)==4
    assert quantile([7,1,5,3],1)==7


def test_positionwise_comparison_rejects_mismatched_word_count():
    with pytest.raises(ValueError):list(windows(records(2,3),2,[5],1,3))
