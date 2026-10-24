from itertools import product
import pytest
from benchmarks import public_length_calibration as b


@pytest.mark.parametrize('profile',b.PROFILES)
def test_frozen_codebooks_prefix_free_and_reproducible(profile):
    symbols=tuple('abcdefghiklmnopqrstuvxyz')
    enc=b.codebook(symbols,tuple('uvwxyz'),profile,3101)
    assert enc==b.codebook(symbols,tuple('uvwxyz'),profile,3101)
    codes=[cs[0] for cs in enc.codebook.values()]
    assert len(codes)==len(symbols)==len(set(codes))
    assert not any(a!=c and c[:len(a)]==a for a,c in product(codes,codes))
    if profile=='mixed-one-two-three':assert set(map(len,codes))=={1,2,3}


def test_generation_changes_seed_without_changing_lengths_profile():
    symbols=tuple('abcdefghiklmnopqrstuvxyz')
    a=b.codebook(symbols,tuple('uvwxyz'),'mixed-one-two-three',3101)
    c=b.codebook(symbols,tuple('uvwxyz'),'mixed-one-two-three',3102)
    assert a!=c
    assert sorted(len(cs[0]) for cs in a.codebook.values())==sorted(len(cs[0]) for cs in c.codebook.values())
