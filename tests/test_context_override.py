import numpy as np
from voynich_smt.context_override import signals,choose,apply,counts,calibrate,ranking


def test_signals_and_gate_use_only_observed_probabilities_and_support():
    ctx=np.array([[.1,.9],[.8,.2],[.4,.6]]);ordinary=np.array([[.9,.1],[.1,.9],[.7,.3]]);support=np.array([[1,1,1],[0,1,1]],bool);f=signals(ctx,ordinary,support,[0,1,2]);p=dict(enabled=True,gate='outside',confidence=.7,ratio=2)
    np.testing.assert_array_equal(choose(f,p),[1,0,0]);pred,m=apply(f,p);np.testing.assert_array_equal(pred,[1,1,0]);assert f['outside_mass'][0]==.9
    p['gate']='disagreement';np.testing.assert_array_equal(choose(f,p),[1,1,0])


def test_no_positive_calibration_gain_disables_even_zero_override_ties():
    f=dict(old=[0,0],new=[1,1],disagree=[True]*2,outside_top=[True]*2,confidence=[.7,.7],ratio=[4.,4.])
    records=[dict(features=f,gold=[0,1],excluded=[False,True])]
    result=calibrate(records,dict(confidence=[.5,.9],ratio=[1.,8.]),risk=1.)
    assert not result['policy']['enabled'] and result['calibration']['overrides']==0


def test_risk_constraint_and_exact_correction_accounting():
    f=dict(old=[0,0,0],new=[1,1,1],disagree=[True]*3,outside_top=[True]*3,confidence=[.9,.9,.7],ratio=[8.,8.,4.]);gold=[1,1,0];excluded=[True,True,False]
    result=calibrate([dict(features=f,gold=gold,excluded=excluded)],dict(confidence=[.5,.8],ratio=[1.]),risk=0.)
    assert result['policy']['enabled'] and result['policy']['confidence']==.8
    c=counts(f,gold,choose(f,result['policy']),excluded);assert c['corrected']==2 and c['spoiled']==0 and c['recovered_excluded']==2


def test_ranking_matches_pairwise_auc_including_ties():
    s=np.array([.9,.5,.5,.1]);y=np.array([1,0,1,0],bool);r=ranking(s,y)
    expected=np.mean([float(a>b)+.5*float(a==b) for a in s[y] for b in s[~y]])
    assert r['auroc']==expected==.875
    np.testing.assert_allclose(r['average_precision'],(1+2/3)/2)
    assert ranking(s,np.ones(4,bool))['auroc'] is None
