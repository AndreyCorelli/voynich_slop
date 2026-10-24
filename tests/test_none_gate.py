import pytest
from voynich_smt.none_gate import best_edge,accept,calibrate
from voynich_smt.multi_link_attachment import propose


def test_negative_edge_can_be_recovered_without_changing_rank():
    frame=dict(predicates=[2,4],vectors={'structural':[[-2.],[-3.]]})
    model=dict(arm='structural',weights=[1.])
    proposal=best_edge(frame,model)
    assert proposal==dict(predicate=2,margin=-2.)
    assert propose(frame,model)['predicate'] is None
    assert not accept(proposal,0) and accept(proposal,-3)


def test_zero_cutoff_preserves_map_ties_and_empty_frames():
    model=dict(arm='structural',weights=[1.])
    for scores in ([],[0.],[-1.],[1.],[1.,1.],[-1.,-1.],[1.,2.]):
        frame=dict(predicates=list(range(len(scores))),vectors={'structural':[[s] for s in scores]})
        proposal=best_edge(frame,model)
        assert (proposal['predicate'] if accept(proposal,0) else None)==propose(frame,model)['predicate']
        if len(scores)==2 and scores[0]==scores[1]:assert proposal['predicate'] is None


def test_calibration_recovers_signal_below_map_cutoff():
    frames=[dict(sid=str(i),subject=0,gold=2 if i<20 else None) for i in range(40)]
    proposals=[dict(predicate=2,margin=-1. if i<20 else -3.) for i in range(40)]
    free=calibrate(frames,proposals,'free');control=calibrate(frames,proposals,'map')
    assert free['f1']['f1']==1 and free['f1']['cutoff']<0
    assert free['precision90']['tp']==20
    assert control['f1']['predicted']==0
    assert control['precision90']['cutoff']==1000000


def test_inference_ignores_targets_and_threshold_keeps_abstentions():
    frame=dict(predicates=[2],vectors={'structural':[[-1.]]},gold=2)
    model=dict(arm='structural',weights=[1.])
    assert best_edge(frame,model)==best_edge(dict(frame,gold=None),model)
    assert not accept(dict(predicate=None,margin=None),-1000000)
    assert not accept(best_edge(frame,model),-1.)


def test_invalid_selection_and_nonfinite_scores_rejected():
    with pytest.raises(ValueError):calibrate([],[],'unknown')
    with pytest.raises(AssertionError):calibrate([{}],[],'free')
    with pytest.raises(AssertionError):best_edge(dict(predicates=[2],vectors={'structural':[[float('nan')]]}),dict(arm='structural',weights=[1.]))
