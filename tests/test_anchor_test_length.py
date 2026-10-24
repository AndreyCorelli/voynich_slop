import pytest
from voynich_smt.anchor_test_length import test_blocks as build_blocks


def test_primary_levels_share_census_and_endpoints_stay_inside_test():
    ids=[str(i) for i in range(770)];blocks=build_blocks(ids)
    assert len(blocks)==9
    census=set(blocks['400-0'])
    for n in (100,200,400):
        level=[v for k,v in blocks.items() if k.startswith(str(n)+'-')]
        assert all(len(v)==n for v in level)
        assert len([sid for v in level for sid in v])==400
        assert {sid for v in level for sid in v}==census
    assert census<=set(blocks['700-0'])<=set(blocks['770-0'])==set(ids)
    assert build_blocks(list(reversed(ids)))['400-0']==blocks['400-0']
    assert ids==[str(i) for i in range(770)]


def test_no_padding_or_duplicate_sentences():
    with pytest.raises(ValueError):build_blocks([str(i) for i in range(699)])
    with pytest.raises(ValueError):build_blocks([str(i) for i in range(769)]+['0'])
