from voynich_smt.unknown_partner_gate import contrast, choose


def test_global_supported_singleton_can_veto_pair():
    f=dict(pair=['a','b'],gain=1.,gap=.5,stability=.9)
    p=dict(threshold=.6,gap=.25,stability=.5)
    unary={'outside_pair':dict(gain=1.2,supported=True),'noise':dict(gain=9.,supported=False)}
    assert abs(contrast(f,unary)+.2)<1e-12
    assert choose(f,unary,p,0.) is None
    assert choose(f,{},p,0.)==['a','b']
    assert choose(f,{},p,None) is None


def test_no_error_alternative_and_missing_pair():
    assert contrast(dict(pair=['a','b'],gain=.4),{'a':dict(gain=-2.,supported=True)})==.4
    assert contrast(dict(pair=None),{}) is None
