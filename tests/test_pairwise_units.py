import numpy as np
import pytest
from voynich_smt.pairwise_units import objective,pairs,fit
from voynich_smt.typed_predicate_units import FEATURES


def frame(options,gold,x):return dict(options=options,gold=gold,x=np.asarray(x,dtype=float))


def test_pairwise_gradient_and_extreme_margins():
    d=np.asarray([[1.,2.],[-2.,1.],[0.,-3.]])
    weights=np.asarray([.25,.25,.5]);w=np.asarray([.2,-.3]);_,g=objective(w,d,weights)
    for i in range(2):
        delta=np.zeros(2);delta[i]=1e-6
        assert abs((objective(w+delta,d,weights)[0]-objective(w-delta,d,weights)[0])/2e-6-g[i])<1e-7
    loss,g=objective(np.asarray([10000.,-10000.]),d,weights)
    assert np.isfinite(loss) and np.isfinite(g).all()


def test_all_pairs_equalize_frames_not_candidate_counts():
    a=frame([(2,'direct'),(1,'cop')],[0,1,2,'cop'],[[0,0],[1,2]])
    b=frame([(2,'direct'),(1,'cop'),(1,'aux')],[0,2,2,'direct'],[[1,0],[0,1],[0,2]])
    d,w,c=pairs([a,b],'pair_all',[0,0])
    assert np.allclose(w,[.5,.25,.25]) and np.allclose(d[0],[1,2])
    assert sum(c.values())==3


def test_hard_opponents_exclude_gold_and_keep_all_ties():
    a=frame([(3,'direct'),(1,'cop'),(2,'cop'),(1,'aux')],[0,1,3,'cop'],[[2,0],[10,0],[2,1],[0,1]])
    d,w,c=pairs([a],'pair_hard',[1,0])
    assert len(d)==2 and np.allclose(w,[.5,.5])
    assert np.allclose(d,[[8,0],[8,-1]])
    assert c=={'cop->direct':1,'cop->cop':1}


def test_fitted_pair_ranker_prefers_gold_and_is_order_invariant():
    x=np.eye(3,len(FEATURES));a=frame([(2,'direct'),(1,'cop'),(1,'aux')],[0,1,2,'cop'],x)
    model=fit([a]*4,'pair_all',np.zeros(len(FEATURES)))
    scores=x@np.asarray(model['weights']);assert scores[1]>max(scores[0],scores[2])
    b=frame(list(reversed(a['options'])),a['gold'],x[::-1]);other=fit([b]*4,'pair_all',np.zeros(len(FEATURES)))
    assert np.allclose(model['weights'],other['weights'])


def test_unknown_mining_mode_is_rejected():
    with pytest.raises(ValueError):pairs([],'test',[])
