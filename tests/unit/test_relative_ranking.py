import numpy as np
from voynich_smt.relative_ranking import fit_ranker,pair_weights


def test_positive_difference_learns_correct_order_without_intercept():
    w=fit_ranker([[1.],[2.]], [1.,1.], .01)
    assert w[0]>0
    assert np.isclose((np.array([6.])@w-np.array([4.])@w),np.array([2.])@w)


def test_signed_can_reverse_misleading_feature():
    signed=fit_ranker([[-1.],[-2.]], [1.,1.], .01,False)
    constrained=fit_ranker([[-1.],[-2.]], [1.,1.], .01,True)
    assert signed[0]<0 and constrained[0]==0


def test_work_balance_not_overridden_by_more_pairs():
    pairs=[{'document':'a','width':250,'kind':'original'}]*20+[{'document':'b','width':250,'kind':'original'}]
    weights=pair_weights(pairs)
    assert np.isclose(sum(weights[:20]),weights[-1])


def test_work_width_kind_cells_have_equal_mass():
    pairs=[{'document':'a','width':250,'kind':'original'}]*3+[{'document':'a','width':250,'kind':'control'}]+[{'document':'a','width':1000,'kind':'original'}]
    weights=pair_weights(pairs)
    assert np.isclose(sum(weights[:3]),weights[3])
    assert np.isclose(sum(weights[:4]),weights[4])
