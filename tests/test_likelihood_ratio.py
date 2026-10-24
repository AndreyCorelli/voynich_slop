import numpy as np
import pytest
from benchmarks.grammar_likelihood_ratio_iteration75 import evidence
P=[('NOUN','Acc','Sing'),('NOUN','Nom','Plur'),('ADV','','')]
PR=np.array([.3,.2,.5])
def test_prior_is_neutral_after_context_only_normalization():
    assert evidence(PR,[('NOUN','','')],[.2],P,PR)==pytest.approx(.2)
    assert evidence(PR,[('NOUN','','')],[.2],P,PR,True)==pytest.approx(1)
def test_specific_profile_uses_posterior_over_prior():
    q=np.array([.6,.1,.3])
    assert evidence(q,[('NOUN','Acc','Sing')],[1],P,PR)==pytest.approx(2)
def test_unresolved_reading_averages_joint_profile_evidence():
    q=np.array([.6,.1,.3])
    assert evidence(q,[('NOUN','','')],[1],P,PR)==pytest.approx(.7/.5)
def test_unknown_and_unsupported_are_zero():
    assert evidence(PR,[],[],P,PR,True)==0
    assert evidence(PR,[('VERB','','')],[1],P,PR,True)==0
