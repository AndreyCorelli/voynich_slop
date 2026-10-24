import numpy as np
from voynich_smt.candidate_abstention import calibrate_flag,flag,abstention_metrics


def test_threshold_matches_independent_exhaustive_search():
    scores=np.array([.9,.8,.8,.7,.4,.1]);excluded=np.array([1,1,0,0,1,0],bool);protected=np.array([0,0,1,1,0,1],bool)
    for budget in (0,.34,.67,1.):
        r=calibrate_flag(scores,excluded,protected,budget);best=None
        for threshold in sorted(set(scores)):
            mask=scores>=threshold;tp=int((mask&excluded).sum());fp=int((mask&protected).sum())
            if tp and fp<=budget*protected.sum():
                key=(tp,-int(mask.sum()),float(threshold))
                if best is None or key>best[0]:best=(key,threshold)
        assert r['enabled']==(best is not None)
        if best is not None:assert r['threshold']==best[1]


def test_ties_cannot_be_split_to_evade_false_flag_budget():
    r=calibrate_flag([.8,.8],[True,False],[False,True],budget=0)
    assert not r['enabled'] and not flag([.8,.8],r).any()
    r=calibrate_flag([.9,.8],[False,False],[True,True],budget=1)
    assert not r['enabled']


def test_abstention_does_not_create_correct_tags():
    r=abstention_metrics([0,1,0,1],[0,0,0,0],[0,1,0,1],[0,1,0,1])
    assert r['retained_accuracy']==1 and r['coverage']==.5 and r['retained_correct_fraction']==.5
    assert r['baseline_correct']==r['retained_correct']==2 and r['excluded_precision']==1 and r['excluded_recall']==1
    empty=abstention_metrics([0],[0],[False],[True]);assert empty['retained_accuracy'] is None and empty['correct_tags_discarded']==1


def test_protected_false_flags_and_corruption_detection_are_separate():
    r=abstention_metrics([0,1,1],[0,0,1],[False,True,True],[True,True,True])
    assert r['flagged_excluded']==2 and r['flagged_errors']==1 and r['correct_tags_discarded']==2
    assert r['false_flags_protected']==1 and r['false_flag_rate_protected']==1
