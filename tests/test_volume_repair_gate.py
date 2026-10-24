from voynich_smt.volume_repair_gate import fit_regimes,route,select_conditional


def stats(hit,wrong=0):return dict(hit=hit,wrong=wrong,calls=hit+wrong,clean_wrong=0,unavailable_wrong=0,n=100)


def test_separate_policies_can_qualify_when_neither_shared_policy_does():
    a=dict(threshold=1.,gap=0.,stability=.75);b=dict(threshold=2.,gap=.25,stability=.5)
    curve=[dict(policy=a,stats=dict(full=stats(12),sparse=stats(1,2)),qualified=False),dict(policy=b,stats=dict(full=stats(0),sparse=stats(20)),qualified=False)]
    chosen=fit_regimes(curve)
    assert chosen['full']['policy']==a and chosen['sparse']['policy']==b
    assert chosen['full']['qualified'] and chosen['sparse']['qualified']


def test_unobserved_volume_band_abstains_and_boundaries_route_exactly():
    bands=dict(maximum_short_sentences=100,minimum_long_sentences=829)
    assert [route(n,bands) for n in [100,101,828,829]]==['sparse',None,None,'full']
    p=dict(threshold=0.,gap=0.,stability=0.);f=dict(pair=['a','b'],gain=1.,gap=.5,stability=1.)
    assert select_conditional(f,500,dict(full=p,sparse=p),bands) is None
    assert select_conditional(f,829,dict(full=p,sparse=p),bands)==['a','b']
