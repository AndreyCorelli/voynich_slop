from benchmarks.cross_window_passages import select_windows


def records():
    out=[]
    for section in 'ABCHPSTZ':
        for i in range(100 if section in 'HS' else 70):
            out.append({'section':section,'folio':'f'+section,'locus':f'{section}.{i//7}',
                        'tokens':[] if i==35 else list('abc')})
    return out


def test_selection_is_deterministic_nonoverlapping_and_ignores_word_scores():
    rows=records();chosen=select_windows(rows)
    assert chosen==select_windows(rows)
    assert len(chosen)==10
    assert {c['section'] for c in chosen}==set('ABCHPSTZ')
    assert [c['section'] for c in chosen].count('H')==2
    assert [c['section'] for c in chosen].count('S')==2
    indices=[k for c in chosen for k in c['record_indices']]
    assert len(indices)==len(set(indices))==220
    for c in chosen:
        ix=c['record_indices']
        assert ix==list(range(ix[0],ix[0]+22))
        assert all(rows[k]['tokens'] for k in ix)
        assert len({rows[k]['folio'] for k in ix})==1
    changed=[{**r,'tokens':list('z') if r['tokens'] else []} for r in rows]
    assert [c['record_indices'] for c in select_windows(changed)]==[c['record_indices'] for c in chosen]


def test_folio_boundary_blocks_windows():
    rows=records()
    # Cut each run into folios shorter than a window: no eligible section remains.
    for i,r in enumerate(rows):r['folio']=f'f{i//10}'
    import pytest
    with pytest.raises(ValueError,match='eight eligible'):
        select_windows(rows)
