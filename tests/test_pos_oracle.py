import numpy as np
from benchmarks.grammar_pos_oracle_iteration72 import condition_pos,within_weights

def test_conditions_joint_labels_without_merging_analyses():
    m={'labels':[['obj',['NOUN','Acc','Sing']],['advmod',['ADV','','']],['nsubj',['NOUN','Nom','Plur']]]}
    assert np.allclose(condition_pos(m,[.2,.6,.2],'NOUN'),[.5,0,.5])
def test_unsupported_pos_remains_zero():
    m={'labels':[['obj',['NOUN','Acc','Sing']]]}
    assert list(condition_pos(m,[1.],'ADJ'))==[0.]
def test_within_weights_remove_word_prior_but_preserve_joint_sets():
    assert within_weights([('ADV','',''),('NOUN','Nom','Sing'),('NOUN','Acc','Plur')],'NOUN')==[0,.5,.5]
def test_missing_correct_pos_not_filled_in():
    assert within_weights([('ADV','','')],'NOUN')==[0.]
