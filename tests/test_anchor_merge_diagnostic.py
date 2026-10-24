import math
from voynich_smt.anchor_merge_diagnostic import eligibility_sets,eligible_pairs,trace_pair,equal_group_gain


def test_eligibility_factorial_ignores_noncore_and_can_override_count_gate():
    sets=eligibility_sets(['a','x'],['b','x'])
    assert sets['intersection']==['x'] and sets['union']==['a','b','x']
    scores=[dict(pair=['i','j'],gain=1.,supported=False),dict(pair=['foreign','j'],gain=2.,supported=True)]
    rows=eligible_pairs(scores,['a','b'],{'i':'a','j':'b'})
    assert rows==[dict(pair=['i','j'],gain=1.,supported=True)]
    assert not scores[0]['supported']


def test_occurrence_logit_trace_and_group_counts():
    model=dict(vocabulary={'centerAnchorTag:X':0},weights=[[0.,math.log(3)]],classes=['ADP','CCONJ'])
    public=[dict(sent_id='s0',tokens=[dict(id='a',anchor='in',tag='ADP'),dict(id='b',anchor='et',tag='CCONJ')]),dict(sent_id='s1',tokens=[dict(id='a',anchor='in',tag='ADP')])]
    t=trace_pair(public,['a','b'],{'a':'ADP','b':'CCONJ'},model,'a',{'s0':'left','s1':'right'})
    assert len(t['focus_occurrences'])==2
    assert all(math.isclose(r['logit'],math.log(3)) for r in t['focus_occurrences'])
    assert t['endpoints'][0]['groups']['left']['n']==1 and t['endpoints'][0]['groups']['right']['n']==1
    assert math.isclose(t['gain'],0.,abs_tol=1e-12)


def test_equal_group_probability_mean_is_not_occurrence_weighted():
    trace=dict(endpoints=[dict(proposed='ADP',groups={'left':dict(n=100,mean=[.8,.2]),'right':dict(n=1,mean=[.2,.8])})])
    assert math.isclose(equal_group_gain(trace),0.,abs_tol=1e-12)
