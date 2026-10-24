import pytest
from voynich_smt.cipher.base import Encoder
from benchmarks.currier_shared_parameters import expected,encode_word

def test_iid_homophone_collision_and_lengths_are_analytic():
    encoder=Encoder({'a':(('x',),('y','z')),'b':(('q',),)})
    m=expected(['aa','aa','b','b'],encoder,'independent',1)
    assert m['mean_word_length']==2
    assert m['within_folio_repeat_pair_rate']==pytest.approx(.3125)
    d=expected(['aa','aa','b','b'],encoder,'word-deterministic',1)
    assert d['within_folio_repeat_pair_rate']==.5
    assert encode_word('aa',encoder,1)==encode_word('aa',encoder,1)

def test_contraction_compact_key_is_prefix_free_and_keeps_frequent_units_short():
    from collections import Counter
    from benchmarks.currier_shared_contractions import compact_key
    book=compact_key(tuple('abcdef'),Counter(a=100,b=50),tuple('wxyz'),7).codebook
    codes=[c for cs in book.values() for c in cs]
    assert len(book['a'][0])==1 and len(book['b'][0])==1
    assert len(codes)==len(set(codes))==6
    assert all(not (len(a)<len(b) and b[:len(a)]==a) for a in codes for b in codes)
