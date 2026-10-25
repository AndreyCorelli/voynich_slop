import itertools
from collections import Counter
from voynich_smt.opaque_context_overlap import statistics


def public(sequences):
    return [dict(tokens=[dict(id=w,anchor='PRIVATE',tag='PRIVATE') for w in seq]) for seq in sequences]


def test_null_matches_exhaustive_count_conditioned_partitions():
    p=public([['a','x','a'],['a','x','b'],['b','x','c']]);r=statistics(p)['x'];pool=['a','a','b','a','b','c'];values=[]
    for ix in itertools.combinations(range(6),3):
        a=Counter(pool[i] for i in ix);b=Counter(pool[i] for i in range(6) if i not in ix);values.append(sum(min(a[w]/3,b[w]/3) for w in set(pool)))
    assert abs(r['null_mean']-sum(values)/len(values))<1e-12
    assert abs(r['overlap']-2/3)<1e-12


def test_renaming_private_fields_and_direction_reversal():
    p=public([['a','x','b'],['c','x','a']]);q=public([['A','X','B'],['C','X','A']]);assert statistics(p)['x']==statistics(q)['X']
    rev=public([['b','x','a'],['a','x','c']]);assert statistics(p)['x']==statistics(rev)['x']


def test_sentence_edges_and_empty_inputs():
    r=statistics(public([['x'],['a','x']]))['x'];assert r['n']==2 and r['left_n']==1 and r['right_n']==0
    assert r['corrected']==0 and not r['supported']
    assert statistics([])=={}
