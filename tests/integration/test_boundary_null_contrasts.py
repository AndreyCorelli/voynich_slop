from collections import Counter
from benchmarks.boundary_mechanisms import encoder, decode
from benchmarks.weak_boundary_calibration import reorder, stream_seed


def blocks():
    return [{'folio':'a','start':0,'words':[list(w) for w in ('ab','ca','ad','da')]*8,'positions':[4]*32,'line_ids':['same']*32}]


def test_weaker_schedules_roundtrip_and_marker_counts():
    original=blocks()
    for dose,expected in ((.0625,1),(.125,3)):
        encoded,key=encoder(original,32001,dose)
        assert decode(encoded,key)==original
        assert sum(len(c)-len(p) for c,p in zip(encoded[0]['words'],original[0]['words']))==expected


def test_shuffle_preserves_encoded_payload_word_inventory_and_lengths():
    encoded,_=encoder(blocks(),32001,.125); shuffled,_=reorder(encoded,0,stream_seed(32101,'heldout'))
    assert Counter(map(''.join,shuffled[0]['words']))==Counter(map(''.join,encoded[0]['words']))
    assert list(map(len,shuffled[0]['words']))==list(map(len,encoded[0]['words']))
    assert shuffled[0]['positions']==encoded[0]['positions']


def test_null_streams_are_distinct_by_split_and_replicate():
    seeds={stream_seed(n,split) for n in (32101,32102,32103) for split in ('train','heldout')}
    assert len(seeds)==6
