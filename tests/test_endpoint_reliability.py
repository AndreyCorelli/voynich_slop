import numpy as np
from voynich_smt.endpoint_reliability import profile,pair_margin,veto


def test_profile_uses_distribution_and_support_without_identity():
    a=profile([.2,.8],2);b=profile([.5,.5],1)
    assert abs(a[0]-b[0])<1e-12 and a[1]>b[1] and a[-1]>b[-1]
    assert np.isfinite(a).all()


def test_weak_endpoint_vetoes_strong_partner():
    p=['a','b'];tags={'a':'ADP','b':'CCONJ'}
    m=pair_margin(p,tags,{'a':.99,'b':.7})
    assert m<0 and veto(p,m,0.) is None
    assert veto(p,m,-2.)==p and veto(p,m,None) is None
    assert pair_margin(p,tags,{'a':.99}) is None
