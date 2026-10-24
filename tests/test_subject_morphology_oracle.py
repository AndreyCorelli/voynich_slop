import pytest
from benchmarks.grammar_subject_morphology_oracle_iteration78 import conditional_subject
M={'labels':[['nsubj',['NOUN','Nom','Sing']],['obj',['NOUN','Acc','Sing']],['appos',['NOUN','Nom','Sing']],['advmod',['ADV','','']]]}
def test_pos_oracle_keeps_case_uncertainty():
    q,ok=conditional_subject(M,[.2,.3,.1,.4],['NOUN','Nom','Sing'],False)
    assert ok and q==pytest.approx(.2/.6)
def test_profile_oracle_conditions_joint_fields():
    q,ok=conditional_subject(M,[.2,.3,.1,.4],['NOUN','Nom','Sing'],True)
    assert ok and q==pytest.approx(2/3)
def test_unsupported_profile_is_explicit_not_backfilled():
    q,ok=conditional_subject(M,[.2,.3,.1,.4],['NOUN','Nom','Plur'],True)
    assert not ok and q==0

def test_empty_feature_is_exact_category_not_wildcard():
    q,ok=conditional_subject(M,[.2,.3,.1,.4],['NOUN','',''],True)
    assert not ok and q==0
