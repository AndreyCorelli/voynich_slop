import numpy as np
from voynich_smt.pooled_grammar import pos_mass,replace_pos,pooled_marginal,task_scores,select_policy
LABELS=[['nsubj',['NOUN','Nom','Sing']],['obj',['NOUN','Acc','Sing']],['advmod',['ADV','','']]]
def test_reweight_preserves_within_pos_conditionals():
    p=replace_pos(LABELS,[.1,.3,.6],{'NOUN':.8,'ADV':.2})
    assert np.allclose(p,[.2,.6,.2])
    assert pos_mass(LABELS,p)=={'NOUN':.8,'ADV':.2}
    assert abs(sum(p)-1)<1e-12

def test_pooling_excludes_current_and_handles_singleton():
    m=[{'NOUN':1},{'ADV':1}]
    assert pooled_marginal(m,[0,1],0)=={'ADV':1}
    assert pooled_marginal(m,[0],0) is None

def test_role_not_made_constant_across_word_occurrences():
    a=replace_pos(LABELS,[.1,.3,.6],{'NOUN':.8,'ADV':.2})
    b=replace_pos(LABELS,[.3,.1,.6],{'NOUN':.8,'ADV':.2})
    assert task_scores(LABELS,a)['subject']<task_scores(LABELS,b)['subject']

def test_no_precision90_policy_without_required_support():
    rows=[dict(word='x',labels={'subject':True},scores={'local':{'subject':.9}})]
    assert select_policy(rows,'subject','local')['precision90'] is None

def test_f1_threshold_selected_only_from_supplied_calibration_rows():
    rows=[dict(word='a',labels={'subject':True},scores={'local':{'subject':.8}}),dict(word='b',labels={'subject':False},scores={'local':{'subject':.2}})]
    p=select_policy(rows,'subject','local')
    assert p['f1']['calibration']['f1']==1
    assert .2<p['f1']['threshold']<=.8
