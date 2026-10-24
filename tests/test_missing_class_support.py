import numpy as np
from voynich_smt.noisy_class_support import support_schedule,noisy_support
from voynich_smt.missing_class_support import deletion_schedule,missing_support,cohorts,token_metrics


def test_nested_deletions_keep_false_fallback_and_remove_true_pairs():
    ref=np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0]],bool);add=support_schedule(ref,7);remove=deletion_schedule(ref,8);previous=noisy_support(ref,add,1.)[0]
    assert remove==deletion_schedule(ref,8)
    for rate in (0,.25,.5,1.):
        mask,affected=missing_support(ref,add,remove,rate)
        assert affected.sum()==int(rate*4);assert mask.any(axis=0).all();assert np.all(previous[mask]);assert int((ref&~mask).sum())==int(rate*4)
        for w in range(4):assert mask[add['extra'][w],w]
        previous=mask


def test_token_coverage_depends_on_gold_class_and_neighbors_respect_boundaries():
    # Type0 admits both0/1 originally; class0 removed but its class1 token remains covered.
    ref=np.array([[1,0],[1,1],[0,0]],bool);support=np.array([[0,0],[1,1],[1,1]],bool)
    sequences=[[0,1],[0,1]];truth=[[0,1],[1,1]];gold,m=cohorts(sequences,truth,support,np.array([1,0],bool),ref,1)
    np.testing.assert_array_equal(m['covered'],[0,1,1,1]);np.testing.assert_array_equal(m['covered_affected'],[0,0,1,0]);np.testing.assert_array_equal(m['covered_neighbors'],[0,1,0,0]);np.testing.assert_array_equal(m['excluded_query'],[0,0,0,0])
    r=token_metrics(np.array([2,1,1,2]),gold,m)
    assert r['all']['correct']==2 and r['covered']['correct']==2 and r['excluded']['correct']==0
    assert r['covered']['accuracy']==2/3
    assert r['covered_neighbors_query']['accuracy'] is None


def test_accuracy_decomposes_into_coverage_and_conditional_accuracy():
    ref=np.eye(3,dtype=bool);support=np.array([[0,0,0],[1,1,0],[0,0,1]],bool);seq=[[0,1,2]];truth=[[0,1,2]];y,m=cohorts(seq,truth,support,np.array([1,0,0],bool),ref,0)
    result=token_metrics([1,1,2],y,m)
    assert result['excluded']['correct']==0
    assert result['all']['accuracy']==result['covered']['tokens']/result['all']['tokens']*result['covered']['accuracy']
