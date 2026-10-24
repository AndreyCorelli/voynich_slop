import numpy as np
from voynich_smt.monotone_class_calibration import fit_offset,apply_offset


def test_intercept_matches_training_mean_and_preserves_order():
    p=[.1,.2,.3,.4];m=fit_offset(p,[0,0,1,1]);q=apply_offset(p,m)
    assert abs(q.mean()-.5)<1e-12
    assert np.all(np.diff(q)>0)


def test_class_balance_and_boundary_probabilities():
    p=[0.,.1,.2,1.];y=[0,0,0,1];m=fit_offset(p,y,True);q=apply_offset(p,m)
    assert abs(q[:3].mean()/2+q[3]/2-.5)<1e-12
    assert np.isfinite(q).all()
