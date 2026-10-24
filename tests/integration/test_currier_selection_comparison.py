from benchmarks.currier_selection_comparison import key_for,encode
from voynich_smt.models.text import Text

def test_fixed_codes_are_distinct_single_atomic_symbols_and_reversible():
    encoder,nulls=key_for(tuple('abcdefghijklmnopqrstuvwxy'),7)
    codes=[c for cs in encoder.codebook.values() for c in cs]
    assert len(codes)==len(set(codes))==50 and all(len(c)==1 for c in codes)
    assert set(nulls).isdisjoint(c[0] for c in codes)
    plain=[[tuple('abb'),tuple('abb')]]
    for mode in ('independent','word-deterministic'):
        payload,gaps=encode(plain,encoder,8,mode)
        assert encoder.decode(Text(tuple(payload[0])))==Text(tuple(plain[0]))
        assert gaps==[[[0,1,2,3],[0,1,2,3]]]

def test_determinism_survives_context_and_word_position_changes():
    encoder,_=key_for(tuple('abc'),19)
    one,_=encode([[tuple('abc'),tuple('abc')]],encoder,20,'word-deterministic')
    two,_=encode([[tuple('c'),tuple('abc')]],encoder,20,'word-deterministic')
    assert one[0][0]==one[0][1]==two[0][1]
