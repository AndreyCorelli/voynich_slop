import pytest
from benchmarks.latin_length_failures import diagnose, mismatch
from benchmarks.latin_contractions import unitizations


def test_too_short_cannot_be_repaired_by_more_contraction():
    paths=unitizations('a', [])
    failure=mismatch('a', paths, 4, 0)
    assert failure['kind']=='too-short'
    assert failure['minimum_unit_gap']==1
    assert failure['additional_contraction_cannot_fix']


def test_optional_counts_prevent_false_failure_from_maximal_contraction():
    rules=[{'id':'est','expansion':'est','position':'whole'}]
    paths=unitizations('est', rules)
    assert mismatch('est', paths, 4, 0) is None
    failure=mismatch('est', paths, 2, 0, maximum_code=1)
    assert failure['kind']=='unattainable-count'
    assert failure['minimum_unit_gap']==1


def test_too_long_distance_and_inclusive_endpoints():
    failure=mismatch('abcde', unitizations('abcde', []), 3, 2)
    assert failure['position']==3 and failure['kind']=='too-long'
    assert failure['minimum_unit_gap']==2
    assert not failure['additional_contraction_cannot_fix']
    assert mismatch('abc',unitizations('abc',[]),3,0) is None
    assert mismatch('a',unitizations('a',[]),3,0) is None


def test_all_positions_are_counted_and_ranking_prefers_fewer_failures():
    result=diagnose([['abcde','abcdef','a']], [], [list('x'),list('y')])
    assert result['failed_position_histogram']=={1:1,2:1}
    assert result['closest_windows'][0]['start_record']==1
    assert result['closest_windows'][0]['total_unit_gap']==5
    assert result['positions'][0]['failures']=={'too-long':2}
    assert result['positions'][1]['failures']=={'too-long':1}


def test_gaps_and_source_boundaries_are_not_bridged():
    result=diagnose([['a',None,'b'],['c']], [], [list('x'),list('y')])
    assert result['windows']==0 and result['minimum_failed_positions'] is None


def test_repetition_filter_is_separate_from_length_ranking():
    result=diagnose([['aa','ab','ab']], [], [list('x'),list('x')])
    assert result['repetition_compatible_windows']==1
    assert result['closest_repetition_compatible_windows'][0]['plaintext']==['ab','ab']
    assert result['closest_windows'][0]['equal_ciphertext_word_conflicts']


def test_contraction_can_fix_lengths_but_never_make_original_words_equal():
    rules=[{'id':'aa','expansion':'aa','position':'whole'},
           {'id':'ab','expansion':'ab','position':'whole'}]
    result=diagnose([['aa','ab']], rules, [list('x'),list('x')])
    assert result['minimum_failed_positions']==0
    assert result['repetition_compatible_windows']==0


def test_ranking_ties_are_broken_by_source_index():
    result=diagnose([['ab','cd','ef']], [], [list('x')],limit=2)
    assert [r['start_record'] for r in result['closest_windows']]==[0,1]
    with pytest.raises(ValueError):
        diagnose([['a']], [], [],limit=1)
