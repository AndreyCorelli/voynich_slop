import numpy as np
from voynich_smt.anchor_stability import stable_scores,select_slack


def test_stability_requires_every_deletion_and_never_adds_calls():
    base=[.9,.85,.7]
    hidden=[[.9,.71,.95],[.5,.9,.95]]
    scores=stable_scores(base,hidden,.8,.1)
    assert np.allclose(scores,[-1,.85,.7])
    assert np.allclose(stable_scores(base,hidden,.8,1.),base)
    assert sum(scores>=.8)==1


def test_calibration_coverage_guard_and_worst_pattern_selection():
    def c(tp,fp):return dict(tp=tp,fp=fp,predicted=tp+fp,precision=tp/(tp+fp))
    curve={'1.0':{'correct':c(100,5),'wrong':c(40,60)},'0.2':{'correct':c(60,2),'wrong':c(30,3)},'0.0':{'correct':c(49,0),'wrong':c(20,0)}}
    assert select_slack(curve)['slack']==.2
    assert select_slack(curve)['qualified']
    assert not select_slack({'1.0':{'correct':c(10,9),'wrong':c(10,9)}})['qualified']
