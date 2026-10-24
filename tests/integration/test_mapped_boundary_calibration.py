from collections import Counter
from benchmarks.mapped_boundary_calibration import reorder, training_mapping, stream_seed


def fixture():
    return [{'folio':'a','start':0,'words':[list(w) for w in ('ay','qa','ay','qa')]*12,'positions':[4]*48,'line_ids':['a']*48}]


def test_mapping_finds_cross_label_dependency():
    mapping,audit=training_mapping(fixture())
    assert mapping['y']=='q' and mapping['a']=='a'
    assert audit['y']['excess_count']>0


def test_mapping_uses_only_supplied_training_events():
    assert training_mapping([{'words':[list('az'),list('qa')], 'positions':[4,4], 'line_ids':['a','b']}])==({}, {})
    assert training_mapping(fixture())==training_mapping(fixture())


def test_reorder_preserves_exact_words_and_respects_mapping():
    b=fixture(); mapping={'y':'q','a':'a'}; out,stats=reorder(b,1,42,mapping)
    assert Counter(map(''.join,b[0]['words']))==Counter(map(''.join,out[0]['words']))
    assert list(map(len,b[0]['words']))==list(map(len,out[0]['words']))
    assert stats['attempted']==stats['eligible'] and stats['matched']==stats['available_matches']
    assert stream_seed(28001,'train')!=stream_seed(28001,'heldout')
