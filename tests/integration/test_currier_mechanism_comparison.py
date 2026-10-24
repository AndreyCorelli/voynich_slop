from collections import Counter
from benchmarks.currier_mechanism_comparison import (
    insert_nulls,resegment,measure,js,correlation,key_for,encode_lines,
)
from voynich_smt.models.text import Text


def test_paired_nulls_preserve_payload_and_match_counts_and_identities():
    payload=[[('a','b'),('c','d')]];gaps=[[[0,1,2],[0,1,2]]]
    (independent,positional),budget=insert_nulls(payload,gaps,('x','y'),0.5,4)
    assert budget==2
    strip=lambda lines:[[tuple(g for g in w if g not in ('x','y')) for w in line] for line in lines]
    assert strip(independent)==strip(positional)==payload
    assert Counter(g for line in independent for w in line for g in w)==Counter(g for line in positional for w in line for g in w)
    assert all(w[-1] in ('x','y') for w in positional[0])


def test_resegmentation_preserves_stream_but_changes_word_cuts():
    payload=[[tuple('abc'),tuple('defgh')],[tuple('ijk')]]
    output=resegment(payload,1,3)
    assert [[g for w in line for g in w] for line in output]==[list('abcdefgh'),list('ijk')]
    assert all(len(w)==1 for line in output for w in line)


def test_metrics_distinguish_tokens_types_and_near_edits():
    m=measure([[tuple('a'),tuple('a'),tuple('ab'),tuple('cd')]])
    assert m['token_lengths']=={1:2,2:2}
    assert m['type_lengths']=={1:1,2:2}
    assert m['repeat_pair_fraction']==1/6
    assert m['near_variant_token_pair_fraction']==2/6
    assert m['near_variant_type_pair_fraction']==1/3
    assert m['token_moments']['variance']==0.25
    assert m['token_moments']['skewness']==0
    assert correlation([(1,2),(2,4),(3,6)])==1
    assert correlation([(1,1),(1,2)]) is None
    assert js({}, {'a':1})==1


def test_prefix_free_payload_and_gap_offsets_are_reversible():
    encoder,nulls=key_for(tuple('abcdef'),tuple('abcdefghijklmnop'),17)
    plain=[[tuple('face'),tuple('bad')]]
    payload,gaps=encode_lines(plain,encoder,18)
    assert encoder.decode(Text(tuple(payload[0])))==Text(tuple(plain[0]))
    assert set(nulls).isdisjoint(g for cs in encoder.codebook.values() for c in cs for g in c)
    for word,offsets in zip(payload[0],gaps[0]):
        assert offsets[0]==0 and offsets[-1]==len(word)
        assert all(1<=b-a<=2 for a,b in zip(offsets,offsets[1:]))
