from voynich_smt.repair_abstention import pair_features,select,calibrate


def case(regime,gain,gap,pair=('a','b'),reference=('a','b'),supported=True,error=True):
    return dict(regime=regime,features=dict(pair=list(pair),gain=gain,gap=gap),reference=dict(error=error,pair=list(reference) if reference else None,supported=supported))


def test_runnerup_gap_does_not_disappear_below_gain_cutoff():
    features=pair_features([dict(pair=['a','b'],gain=1.,supported=True),dict(pair=['c','d'],gain=.95,supported=True)])
    assert select(features,.98,.1) is None
    assert select(features,.98,0)==['a','b']
    assert pair_features([dict(pair=['a','b'],gain=1.,supported=True),dict(pair=['c','d'],gain=1.,supported=True)])['pair'] is None


def test_unavailable_partner_budget_can_require_margin_or_off():
    cases=[case('full',1.,.3) for _ in range(12)]+[case('sparse',1.,.3) for _ in range(24)]
    cases += [case('sparse',1.5,.05,reference=None,supported=False),case('full',.8,.4,reference=None,error=False)]
    absolute,_=calibrate(cases,False)
    margin,_=calibrate(cases,True)
    assert not absolute['qualified'] and absolute['threshold'] is None
    assert margin['qualified'] and margin['threshold']==1. and margin['gap']==.1
    assert margin['stats']['sparse']['unavailable_wrong']==0


def test_minimum_support_rejects_trivial_perfect_policy():
    policy,_=calibrate([case('full',2.,1.),case('sparse',2.,1.)],True)
    assert policy['threshold'] is None and not policy['qualified']
