import pytest
from benchmarks.grammar_context_prediction_iteration74 import probability_record,metrics
M={'labels':[['obj',['NOUN','Acc','Sing']],['obl',['NOUN','Acc','Sing']],['nsubj',['NOUN','Nom','Plur']],['advmod',['ADV','','']]]}
P=[('ADV','',''),('NOUN','Acc','Sing'),('NOUN','Nom','Plur')]
def test_marginalizes_roles_and_conditions_pos():
    r=probability_record(M,[.1,.2,.1,.6],['NOUN','Acc','Sing'],P)
    assert r['pos_probability']==pytest.approx(.4)
    assert r['joint_probability']==pytest.approx(.3)
    assert r['conditional_probability']==pytest.approx(.75)
    assert not r['pos_correct'] and r['conditional_correct']
def test_unsupported_profile_not_dropped():
    r=probability_record(M,[.1,.2,.1,.6],['NOUN','Dat','Sing'],P)
    assert r['joint_probability']==0 and r['conditional_probability']==0
    rows=[{'predictions':{'context':r}}]
    assert metrics(rows,'conditional','context')['zero_probability']==1
    assert metrics(rows,'conditional','context')['nll']>27

def test_loss_chain_rule_for_supported_profile():
    r=probability_record(M,[.1,.2,.1,.6],['NOUN','Acc','Sing'],P)
    assert r['joint_probability']==pytest.approx(r['pos_probability']*r['conditional_probability'])
