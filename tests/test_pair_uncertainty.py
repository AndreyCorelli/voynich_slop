import numpy as np
from voynich_smt.pair_uncertainty import gains_from_totals,summarize,selected,calibrate


def test_sentence_aggregation_preserves_occurrence_weights_and_missing_is_invalid():
    n=np.array([[2,1],[0,3]]);s=np.array([[1.8,.2],[0,.6]])
    g=gains_from_totals(n.sum(0),s.sum(0),['ADP','CCONJ'])
    assert np.isclose(g,np.log((.9+1e-12)/(.1+1e-12))-np.log((.2+1e-12)/(.8+1e-12)))
    assert np.isneginf(gains_from_totals(n[1],s[1],['ADP','CCONJ']))


def test_missing_and_tied_bootstrap_winners_count_as_instability():
    pairs=[dict(pair=['a','b'],gain=2.,supported=True),dict(pair=['a','c'],gain=1.,supported=True)]
    f=summarize(pairs,np.array([[2,1],[1,1],[-np.inf,1],[3,1]]))
    assert f['stability']==.5 and f['valid_fraction']==.75 and f['lower_gain'] is None
    assert selected(f,dict(arm='stability',threshold=0,stability=.75)) is None
    assert selected(f,dict(arm='lower',threshold=0)) is None


def test_calibration_rejects_stable_systematic_wrong_pairs():
    f=dict(pair=['a','b'],gain=2.,gap=1.,stability=1.,lower_gain=1.,lower_gap=.5)
    cases=[dict(regime=r,features=f,reference=dict(pair=['x','y'],error=True,supported=True)) for r,n in [('full',10),('sparse',20)] for _ in range(n)]
    for arm in ['stability','lower']:
        chosen,_=calibrate(cases,arm);assert chosen['policy']['threshold'] is None
