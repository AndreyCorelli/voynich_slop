import numpy as np
from benchmarks.grammar_normalized_readings_iteration73 import reading_distribution,normalized_score,collapse
P=[('NOUN','Acc','Sing'),('NOUN','Nom','Plur'),('ADV','','')]
PR=np.array([.3,.2,.5])
def test_unspecified_reading_has_unit_probability_not_full_posterior_mass():
    q=reading_distribution(('NOUN','',''),P,PR)
    assert np.allclose(q,[.6,.4,0]) and abs(sum(q)-1)<1e-12
    assert normalized_score(np.array([1.,0,0]),[('NOUN','','')],[1],P,PR)==.6

def test_specific_reading_retains_joint_profile():
    assert np.allclose(reading_distribution(('NOUN','Acc','Sing'),P,PR),[1,0,0])
    assert not reading_distribution(('NOUN','Acc','Plur'),P,PR).any()

def test_nonapplicable_adverb_features_stay_empty():
    assert np.allclose(reading_distribution(('ADV','',''),P,PR),[0,0,1])

def test_unknown_and_unsupported_remain_zero():
    assert normalized_score(PR,[],[],P,PR)==0
    assert normalized_score(PR,[('VERB','','')],[1],P,PR)==0

def test_collapse_does_not_count_roles_as_distinct_profiles():
    m={'labels':[['obj',['NOUN','Acc','Sing']],['obl',['NOUN','Acc','Sing']],['advmod',['ADV','','']]]}
    assert np.allclose(collapse(m,[.2,.3,.5],P),[.5,0,.5])
