from benchmarks.latin_pattern_natural_replication import select_passages


def test_passages_contiguous_nonoverlapping_and_no_coverage_selection():
    block = [{'tokens': list(w)} for w in ['abcd']*24 + ['ac','ad','bc','bd','ca','da']]
    records = block * 3
    passages = select_passages(records, 0, set('abcd'))
    assert [p['record_start'] for p in passages] == [0,30,60]
    for p in passages:
        assert len(p['source_records']) == 30 and len(p['train']) == 24 and len(p['held']) == 6
        assert p['source_records'] == records[p['record_start']:p['record_end_exclusive']]
        assert len(set(p['held']) - set(p['train'])) >= 3
