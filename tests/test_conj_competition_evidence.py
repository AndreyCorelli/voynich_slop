import numpy as np
import pytest
from voynich_smt.conj_competition_evidence import adjust_contests
from voynich_smt.joint_subject_none import decode


def fixture():
    tokens=[dict(pos='NOUN'),dict(pos='PROPN'),dict(pos='PRON')];model=dict(mode='pos',vocabulary={'pos:NOUN':0,'pos:PROPN':1,'pos:PRON':2},weights=[-2.,2.,0.]);return tokens,model


def test_relative_evidence_protects_best_phrase_head_and_penalizes_rival():
    tokens,model=fixture();frames=[dict(subject=0,predicates=[5],scores=[2.]),dict(subject=1,predicates=[5],scores=[3.])];new=adjust_contests(frames,tokens,model,2,0)
    assert new[0]['scores']==[2.] and new[1]['scores'][0]<0
    assert decode(new,0,4)[0]=={0:5,1:None}


def test_uncontested_carrier_scores_and_whole_uncontested_sentence_stay_unchanged():
    tokens,model=fixture();frames=[dict(subject=0,predicates=[5,6],scores=[2.,1.]),dict(subject=1,predicates=[5,6],scores=[3.,.5])];new=adjust_contests(frames,tokens,model,2,0)
    assert [r['scores'][1] for r in new]==[1.,.5]
    single=[frames[0]];assert adjust_contests(single,tokens,model,2,0)==single


def test_zero_weight_is_exact_and_does_not_require_token_or_model_access():
    frames=[dict(subject=0,predicates=[5],scores=[2.])];assert adjust_contests(frames,None,None,0,0)==frames


def test_original_best_tie_cannot_be_activated_by_relative_edge_changes():
    tokens,model=fixture();frames=[dict(subject=0,predicates=[5],scores=[2.]),dict(subject=1,predicates=[5],scores=[3.]),dict(subject=2,predicates=[5,6],scores=[2.,2.])];new=adjust_contests(frames,tokens,model,2,0)
    assert new[2]['predicates']==[] and decode(new,0,4)[0][2] is None


def test_evidence_never_boosts_scores_and_never_uses_gold_labels():
    tokens,model=fixture();frames=[dict(subject=0,predicates=[5],scores=[2.],gold=5),dict(subject=1,predicates=[5],scores=[3.],gold=None)];new=adjust_contests(frames,tokens,model,1,0)
    other=[dict(r,gold='hidden') for r in frames];masked=adjust_contests(other,tokens,model,1,0)
    for a,b,c in zip(frames,new,masked):assert np.all(np.asarray(b['scores'])<=a['scores']) and b['scores']==c['scores']
    with pytest.raises(ValueError):adjust_contests(frames,tokens,model,-1,0)
