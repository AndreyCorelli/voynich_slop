from copy import deepcopy
import pytest
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider,score_audit
from voynich_smt.marker_structure import MarkerModel,validate_markers
from tests.unit.test_marker_structure import Constant
from tests.unit.test_predicate_structure import Adapter


def test_scope_oracle_preserves_vocabulary_and_ambiguous_classes():
    learned=MarkerModel({'et':['coordination','subordination']},Constant())
    oracle=OracleMarkerProvider(learned,{1:{'target':2,'kind':'coordination'},3:{'target':4,'kind':'relative'}},'oracle_scope')
    rows=oracle.predict(['a','et','b','qui','c'],[0,2,4],Adapter())
    assert len(rows)==1 and rows[0]['target']==2
    assert rows[0]['kinds']==['coordination','subordination']


def test_full_oracle_adds_missing_markers_and_resolves_reference_kind():
    learned=MarkerModel({'et':['coordination','subordination']},Constant())
    oracle=OracleMarkerProvider(learned,{1:{'target':2,'kind':'coordination'},3:{'target':4,'kind':'relative'}},'oracle_full')
    rows=oracle.predict(['a','et','b','qui','c'],[0,2,4],Adapter())
    assert [(r['position'],r['target'],r['kinds']) for r in rows]==[(1,2,['coordination']),(3,4,['relative'])]
    assert all(sum(x['probability'] for x in r['alternatives'])==1 for r in rows)


def test_missing_predicate_and_conflicting_marker_role_are_not_injected():
    learned=MarkerModel({'et':['coordination']},Constant())
    oracle=OracleMarkerProvider(learned,{1:{'target':2,'kind':'coordination'}},'oracle_scope')
    absent=oracle.predict(['a','et','b'],[0],Adapter())[0]
    assert absent['target'] is None and absent['blocked_reference_target']
    conflict=oracle.predict(['a','et','b'],[0,1,2],Adapter())[0]
    assert conflict['target'] is None and conflict['blocked_reference_target']


def test_nonmarker_occurrence_becomes_null_without_parent_information():
    learned=MarkerModel({'et':['coordination']},Constant())
    oracle=OracleMarkerProvider(learned,{},'oracle_scope')
    assert oracle.predict(['a','et','b'],[0,2],Adapter())[0]['target'] is None
    with pytest.raises(ValueError):OracleMarkerProvider(learned,{},'incorrect')


def fixture():
    gold={'finite':[0,1],'parents':{0:None,1:0},'relations':{0:'root',1:'subordination'}}
    prediction={'status':'optimal','predicates':[0,1],'parents':{0:None,1:None},'relations':{0:'root',1:'root'},
        'forest_score_integer':3000000,'arc_candidates':{
            0:[{'parent':None,'relation':'root','logit':1.},{'parent':1,'relation':'subordination','logit':0.}],
            1:[{'parent':None,'relation':'root','logit':2.},{'parent':0,'relation':'subordination','logit':0.}]}}
    return prediction,gold


def test_exact_reference_forest_gap_and_local_misranking():
    prediction,gold=fixture();audit=score_audit(prediction,gold)
    assert audit['reference_forest_available'] and audit['reference_score_integer']==1000000
    assert audit['optimum_minus_reference_integer']==2000000
    assert audit['strict_local_parent_misrankings']==1
    assert audit['error_counts']=={'correct_parent':1,'false_root':1}


def test_abstention_has_no_claimed_forest_gap():
    prediction,gold=fixture();prediction['status']='unresolved';prediction['forest_score_integer']=None
    audit=score_audit(prediction,gold)
    assert audit['optimum_minus_reference_integer'] is None
    assert audit['error_counts']=={'unresolved':2}
