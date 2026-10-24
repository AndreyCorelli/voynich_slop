"""Fixed-family enumerative encoding of a 24-letter permutation in 10 bytes."""
import math
from voynich_smt.letter_discovery import SPACE
KEY_BYTES=(math.factorial(SPACE).bit_length()+7)//8


def pack_key(key):
    key=[int(v) for v in key]
    if sorted(key)!=list(range(SPACE)):raise ValueError('A complete bijective key is required')
    remaining=list(range(SPACE));rank=0
    for i,value in enumerate(key):
        j=remaining.index(value);rank+=j*math.factorial(SPACE-1-i);remaining.pop(j)
    return rank.to_bytes(KEY_BYTES,'big')


def unpack_key(data):
    if len(data)!=KEY_BYTES:raise ValueError('Incorrect fixed key length')
    rank=int.from_bytes(data,'big')
    if rank>=math.factorial(SPACE):raise ValueError('Permutation rank out of range')
    remaining=list(range(SPACE));key=[]
    for i in range(SPACE):
        j,rank=divmod(rank,math.factorial(SPACE-1-i));key.append(remaining.pop(j))
    return key
