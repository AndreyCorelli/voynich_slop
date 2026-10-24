import numpy as np
import pytest
from voynich_smt.noisy_class_support import support_schedule,noisy_support,subset_score


def test_nested_noise_retains_reference_and_adds_one_false_class():
    reference=np.zeros((4,20),bool);reference[np.arange(20)%4,np.arange(20)]=True;reference[1,0]=True
    schedule=support_schedule(reference,7);previous=reference
    for rate in (0,.01,.1,.25,.5,1.):
        mask,affected=noisy_support(reference,schedule,rate)
        assert np.all(mask[reference]);assert np.all(mask[previous]);assert affected.sum()==int(rate*20)
        np.testing.assert_array_equal((mask&~reference).sum(axis=0),affected.astype(int));previous=mask
    assert support_schedule(reference,7)==schedule
    assert support_schedule(reference,8)!=schedule
    with pytest.raises(ValueError):noisy_support(reference,schedule,1.1)


def test_noise_relabels_equivariantly_given_schedule():
    reference=np.array([[1,0,1],[0,1,0],[0,0,0]],bool);schedule=support_schedule(reference,7);order=[2,0,1];inverse=np.argsort(order)
    changed=dict(schedule,extra=[int(inverse[x]) for x in schedule['extra']]);a,_=noisy_support(reference,schedule,1.);b,_=noisy_support(reference[order],changed,1.)
    np.testing.assert_array_equal(a[order],b)


def test_subset_scores_exclude_unaffected_and_handle_empty():
    gamma=[np.eye(3)[[0,1,0,2]]];truth=[[0,2,0,2]];seq=[[0,1,0,2]]
    r=subset_score(gamma,truth,seq,[False,True,True]);assert r['tokens']==2 and r['correct']==1 and r['accuracy']==.5 and r['balanced_accuracy']==.5
    empty=subset_score(gamma,truth,seq,[False]*3);assert empty['tokens']==0 and empty['accuracy'] is None
