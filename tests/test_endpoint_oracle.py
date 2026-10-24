from copy import deepcopy
import pytest
from voynich_smt.endpoint_oracle import state,flags,allows,masked_frame,false_positive_class


def tokens(case='Nom',form='Fin'):
    return [dict(features={'Case':case}),dict(features={'VerbForm':form}),dict(features={'VerbForm':'Inf'})]


def test_missing_and_ambiguous_annotations_are_permissive_only_when_possible():
    assert state('','Nom')=='unknown'
    assert allows('case',tokens(case=''),0,1,None)
    assert allows('case',tokens(case='Nom,Acc'),0,1,None)
    assert not allows('case',tokens(case='Acc,Abl'),0,1,None)
    assert allows('finite',tokens(form=''),0,1,None)
    assert not allows('finite',tokens(form='Part'),0,1,None)


def test_case_finiteness_and_role_are_distinct_oracles():
    ts=tokens(case='Acc')
    assert not allows('case',ts,0,1,None)
    assert allows('finite',ts,0,1,None)
    assert not allows('subject_role',ts,0,1,None)
    assert allows('subject_role',ts,0,2,1)
    assert not allows('subject_role_finite',ts,0,2,1)
    assert not allows('exact_edge',ts,0,2,1)
    assert allows('exact_edge',ts,0,1,1)


def test_masks_preserve_score_vectors_and_do_not_inject_gold():
    ts=tokens();frame=dict(subject=0,gold=1,predicates=[1,2],vectors={'local_morph':[[1.,2.],[3.,4.]],'structural':[[5.],[6.]]})
    original=deepcopy(frame);result=masked_frame(frame,ts,'finite')
    assert frame==original
    assert result['predicates']==[1]
    assert result['vectors']==dict(local_morph=[[1.,2.]],structural=[[5.]])
    assert masked_frame(dict(frame,gold=9),ts,'exact_edge')['predicates']==[]


def test_taxonomy_does_not_double_count_overlapping_errors():
    ts=tokens(case='Acc')
    assert false_positive_class(ts,0,2,None)=='non_nominative_not_finite_subject/nonfinite'
    assert false_positive_class(tokens(),0,1,None)=='nominative_not_finite_subject/finite'
    assert false_positive_class(tokens(),0,2,1)=='finite_subject_wrong_attachment/nonfinite'
    f=flags(ts,0,2,None)
    assert not f['case_allowed'] and not f['finite_allowed']
    with pytest.raises(ValueError):allows('unknown',ts,0,1,None)
