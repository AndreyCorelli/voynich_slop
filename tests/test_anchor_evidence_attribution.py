import math
from voynich_smt.anchor_evidence_attribution import endpoint


def test_class_flip_and_context_change_are_separate():
    r=endpoint(.2,.2,'ADP','CCONJ')
    assert r['class_changed'] and r['context_invariant']
    assert math.isclose(r['clean_context_proposed_margin'],-r['clean_flip_margin'])
    assert r['corrupt_flip_margin']>0 and not r['preexisting_false_flip']


def test_preexisting_false_signal_versus_new_false_signal():
    old=endpoint(.6,.6,'ADP','ADP')
    assert old['preexisting_false_flip'] and old['observed_false_flip'] and old['context_invariant']
    new=endpoint(.4,.6,'ADP','ADP')
    assert not new['preexisting_false_flip'] and new['observed_false_flip'] and not new['context_invariant']
