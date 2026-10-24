from benchmarks.manuscript_width_audit import input_counts, summarize


def record(length,folio='a',excluded=None):
    return {'tokens':['a']*length,'folio':folio,'excluded_reason':excluded}


def test_divisibility_and_mixed_widths():
    assert input_counts(5,(2,))==[]
    assert input_counts(6,(2,))==[3]
    assert input_counts(1,(2,3))==[]
    assert input_counts(5,(2,3))==[2]
    assert input_counts(5,(1,2,3))==[2,3,4,5]


def test_windows_do_not_bridge_exclusions_or_folios():
    records=[record(2),record(2,excluded='uncertain'),record(2),record(2,'b'),record(2,'b')]
    result=summarize(records,size=2)
    assert result['windows']==1 and result['excluded_records']==1
    assert result['profiles']['fixed-2']['compatible_22_word_windows']==1


def test_odd_word_excludes_fixed_two_window_without_discarding_word():
    result=summarize([record(2),record(3)],size=2)
    assert result['included_word_occurrences']==2
    assert result['profiles']['fixed-2']['compatible_word_occurrences']==1
    assert result['profiles']['fixed-2']['compatible_22_word_windows']==0
    assert result['profiles']['mixed-1-2']['compatible_22_word_windows']==1
