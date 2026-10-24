import math
import numpy as np
import pytest
from voynich_smt.letter_discovery import SPACE
from voynich_smt.letter_key_codec import pack_key,unpack_key,KEY_BYTES


def test_actual_compact_serialization_roundtrips_independent_keys():
    assert KEY_BYTES==10
    for seed in range(10):
        key=np.random.default_rng(seed).permutation(SPACE).tolist();packed=pack_key(key)
        assert len(packed)==10 and unpack_key(packed)==key
    assert unpack_key(pack_key(list(range(SPACE))))==list(range(SPACE))


def test_invalid_permutations_and_unused_codes_are_rejected():
    with pytest.raises(ValueError):pack_key([0]*SPACE)
    with pytest.raises(ValueError):unpack_key(b'')
    with pytest.raises(ValueError):unpack_key(math.factorial(SPACE).to_bytes(KEY_BYTES,'big'))
