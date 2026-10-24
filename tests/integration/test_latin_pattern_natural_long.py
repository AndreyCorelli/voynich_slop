from benchmarks.latin_pattern_natural_long import select_passages


def test_fresh_blocks_have_48_training_and_six_covered_novel_holdouts():
    block = [{'tokens': list(w)} for w in ['abcd']*48 + ['ac','ad','bc','bd','ca','da']]
    records = block * 3
    passages = select_passages(records, 0, set('abcd'))
    assert [p['record_start'] for p in passages] == [0,54,108]
    for p in passages:
        assert len(p['source_records']) == 54 and len(p['train']) == 48 and len(p['held']) == 6
        assert p['source_records'] == records[p['record_start']:p['record_end_exclusive']]
        assert len(set(p['held']) - set(p['train'])) >= 3
        assert set(''.join(p['held'])) <= set(''.join(p['train']))
