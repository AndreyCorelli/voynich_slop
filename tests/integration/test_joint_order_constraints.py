import itertools
from statistics import mean
from benchmarks.joint_order_constraints import optimize, mapped_measure


def fixture(words):
    return {'words':[list(w) for w in words],'positions':[4]*len(words),'line_ids':['a']*len(words)}


def test_joint_beam_attains_small_known_optimum():
    b=fixture(['ab','ab','ba','ba']); mapping={'b':'b','a':'a'}
    result=optimize([b],mapping,7,True)[0]
    assert sorted(result['words'])==sorted(b['words'])
    assert all(a!=z for a,z in zip(result['words'],result['words'][1:]))
    assert mapped_measure([result],mapping)['adjusted']>0


def test_mapped_expectation_matches_exhaustive_null():
    b=fixture(['ab','ab','ba','cc']); mapping={'b':'b','a':'a','c':'c'}
    permutations=list(itertools.permutations(b['words']))
    assert abs(mean(mapped_measure([{**b,'words':list(words)}],mapping)['adjusted'] for words in permutations))<1e-12
