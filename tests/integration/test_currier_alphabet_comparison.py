from collections import Counter
import pytest
from benchmarks.currier_alphabet_comparison import allocation,key_for,encode

def test_capacity_allocation_frequency_and_tie_rule():
    assert allocation('abcd',dict(a=1,b=3,c=3,d=0),6,True)==dict(a=1,b=2,c=2,d=1)
    assert allocation('abcd',Counter(),4,True)==dict(a=1,b=1,c=1,d=1)
    assert allocation('abcd',Counter(),6,False)==dict(a=1,b=1,c=1,d=1)
    with pytest.raises(ValueError):allocation('abcd',Counter(),3,True)

def test_mono_selection_is_identical_and_homophones_are_reversible():
    plain=[[tuple('ababa'),tuple('ababa')]]
    mono=key_for({'a':1,'b':1},tuple('xyz'),7)
    assert encode(plain,mono,8,'independent')==encode(plain,mono,8,'word-deterministic')
    hom=key_for({'a':2,'b':1},tuple('xyz'),7)
    out=encode(plain,hom,8,'word-deterministic')
    assert out[0][0]==out[0][1] and len(out[0][0])==5
    assert len({c[0] for cs in hom.codebook.values() for c in cs})==3
