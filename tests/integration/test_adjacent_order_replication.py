import itertools
from statistics import mean
from benchmarks.adjacent_order_replication import measure, order
from collections import Counter


def test_exact_expectation_matches_exhaustive_mixed_pools():
    b={'words':[list(w) for w in ('a','a','b','a','b','b')],'positions':[1,4,1,4,1,4],'line_ids':['x']*6}
    groups=([0,2,4],[1,3,5]); totals=[]
    for a in itertools.permutations([b['words'][i] for i in groups[0]]):
        for z in itertools.permutations([b['words'][i] for i in groups[1]]):
            words=[None]*6
            for indices,values in zip(groups,(a,z)):
                for i,w in zip(indices,values): words[i]=w
            totals.append(measure({**b,'words':words})['observed_repeat'])
    assert abs(mean(totals)-measure(b)['expected_repeat'])<1e-12


def test_no_duplicate_inventory_cannot_create_exact_repeats():
    b={'words':[list(w) for w in ('ab','ba','ac','ca')],'positions':[4]*4,'line_ids':['x']*4}
    for kind in ('prose','random','mapped','repeat','avoid'):
        generated=order([b],kind,{'b':'b','a':'a'},42)[0]
        assert measure(generated)['adjusted']==0
        assert Counter(map(''.join,generated['words']))==Counter(map(''.join,b['words']))


def test_repeat_avoidance_can_mimic_repeat_suppression():
    b={'words':[list(w) for w in ('a','a','b','b')],'positions':[4]*4,'line_ids':['x']*4}
    generated=order([b],'avoid',{},42)[0]
    assert measure(generated)['observed_repeat']==0 and measure(generated)['adjusted']<0
