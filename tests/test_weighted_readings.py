import pytest
from benchmarks.grammar_weighted_readings_iteration71 import weights,weighted_mass
PM={'words':{'non':{'ADV':100}},'prior':{'ADV':100,'NOUN':100}}
def test_rare_reading_cannot_absorb_common_pos_mass():
    assert weights('non',[('NOUN','','')],PM)==pytest.approx([.5/101])
def test_unseen_uses_prior_without_dictionary_renormalization():
    assert weights('new',[('NOUN','Nom','Sing')],PM)==[.5]
def test_split_pos_weight_over_joint_readings():
    w=weights('new',[('NOUN','Nom','Sing'),('NOUN','Acc','Plur')],PM)
    assert w==[.25,.25]
def test_unknown_remains_zero():
    assert weights('new',[],PM)==[]
    assert weighted_mass({'labels':[['obj',['NOUN','Acc','Sing']]]},[1],[],[])==0
