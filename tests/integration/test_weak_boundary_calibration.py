from collections import Counter
from benchmarks.weak_boundary_calibration import reorder, stream_seed


def fixture():
    return [{'folio':'a','start':0,'words':[list(w) for w in ('ab','ba','ac','ca','bb','cc')], 'positions':[4]*6,'line_ids':['a']*6}]


def test_reordering_preserves_inventory_layout_and_slot_lengths():
    source=fixture()
    for rate in (0,.25,.5,1):
        out,stats=reorder(source,rate,42)
        assert Counter(map(''.join,out[0]['words']))==Counter(map(''.join,source[0]['words']))
        assert list(map(len,out[0]['words']))==list(map(len,source[0]['words']))
        assert out[0]['positions']==source[0]['positions'] and out[0]['line_ids']==source[0]['line_ids']
        assert stats['eligible']==5
    assert ''.join(source[0]['words'][0])=='ab'


def test_maximum_matching_takes_available_candidates():
    _,stats=reorder(fixture(),1,42)
    assert stats['attempted']==stats['eligible']
    assert stats['matched']>=stats['available_matches']


def test_split_streams_differ_and_resume_is_deterministic():
    assert stream_seed(27001,'train')!=stream_seed(27001,'heldout')
    assert reorder(fixture(),.25,stream_seed(27001,'train'))==reorder(fixture(),.25,stream_seed(27001,'train'))
