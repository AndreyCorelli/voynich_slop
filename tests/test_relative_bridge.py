"""Mechanism tests include mixed-reading and non-singleton candidate traps."""
import pytest
from voynich_smt.relative_bridge import BridgeAdapter,bridge,role
from voynich_smt.grammar_diagnostic import MorphAnalysis
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from benchmarks.grammar_relative_bridge_iteration14 import CONTROLLED

@pytest.fixture(scope='module')
def adapter():
    return BridgeAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))

@pytest.mark.parametrize('name,text,predicates,marker,child,expected',CONTROLLED)
def test_controlled(adapter,name,text,predicates,marker,child,expected):
    assert len(predicates)>=3
    result=bridge(text.split(),predicates,marker,child,adapter)
    assert result['parents']==expected
    assert (result['status']=='unique_parent')==(len(expected)==1)
    assert all(w['nominal']==w['governing_nominal'] for w in result['bridges'])

def test_mixed_reading_false_bridge(adapter):
    _,text,predicates,marker,child,_=CONTROLLED[4]
    bad=bridge(text.split(),predicates,marker,child,adapter,consistent=False)
    assert bad['parents']==[1]
    assert bad['bridges'][0]['nominal']!=bad['bridges'][0]['governing_nominal']

def test_person_government(adapter):
    noun=next(r for r in adapter.analyze('ego') if r.pos=='PRON' and r.get('Case')=='NOM')
    singular3=next(r for r in adapter.analyze('currit') if r.pos=='V')
    singular1=next(r for r in adapter.analyze('curro') if r.pos=='V')
    assert role(noun,singular3,['ego'],0,adapter) is None
    assert role(noun,singular1,['ego'],0,adapter)=='subject'

def test_sentence_boundary_is_explicit_oracle(adapter):
    _,text,predicates,marker,child,_=CONTROLLED[5]
    assert bridge(text.split(),predicates,marker,child,adapter)['parents']==[1,8]
    assert bridge(text.split(),predicates,marker,child,adapter,boundaries=[2,9])['parents']==[8]

def test_case_need_not_match(adapter):
    _,text,predicates,marker,child,_=CONTROLLED[1]
    witness=bridge(text.split(),predicates,marker,child,adapter)['bridges'][0]
    assert dict(witness['pronoun']['features'])['Case']=='NOM'
    assert dict(witness['nominal']['features'])['Case']=='ACC'

def test_deponent_label_is_not_transitivity(adapter):
    # DEP supplies voice behavior, not an independently known object frame.
    noun=next(r for r in adapter.analyze('puellam') if r.pos=='N')
    verb=next(r for r in adapter.analyze('patieris') if r.pos=='V')
    assert verb.get('VerbKind')=='DEP'
    assert role(noun,verb,['puellam'],0,adapter) is None
