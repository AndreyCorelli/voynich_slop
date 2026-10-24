from benchmarks.currier_mechanism_discrimination import classify,distance,standardizer,quantile95

def test_rejection_for_ties_and_outside_support():
    model={'centers':[0],'scales':[1],'centroids':{'a':[0],'b':[2]},'radii':{'a':1,'b':1}}
    assert classify([0],model,[0])['prediction']=='a'
    assert classify([1],model,[0])['prediction']=='unresolved'
    assert classify([10],model,[0])['prediction']=='unresolved'

def test_equal_group_weights_and_missing_training_values():
    assert distance([0,0,0],[2,2,4],[0,0,1])==10
    c,s=standardizer([{'features':[1,None]},{'features':[3,None]}])
    assert c==[2,0] and s==[1,1]
    assert quantile95(list(range(20)))==18
