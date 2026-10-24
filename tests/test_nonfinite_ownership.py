import pytest
import z3
from voynich_smt.nonfinite_ownership import Ownership,filter_bridges,crosses
from voynich_smt.relative_constituents import ConstituentAdapter,infer
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from benchmarks.grammar_nonfinite_ownership_iteration16 import PROBES,arguments

@pytest.fixture(scope='module')
def adapter():return ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))

@pytest.mark.parametrize('probe',PROBES,ids=[p[0] for p in PROBES])
def test_fixed_probes(adapter,probe):
    t,p,scopes,expected=arguments(probe)
    assert len(p)>=3
    result=Ownership(t,p,adapter,scopes=scopes,boundaries=(len(t),)).records
    assert {r['position']:{k:r[k] for k in ('possible_parents','status')} for r in result}==expected


def test_farther_owner_beats_distance_in_one_sentence(adapter):
    t,p,s,_=arguments(PROBES[1]);o=Ownership(t,p,adapter,scopes=s,boundaries=(len(t),))
    record=next(r for r in o.records if t[r['position']]=='laborare')
    assert record['nearest_parents']==[t.index('debet')]
    assert record['possible_parents']==[t.index('creditur')]
    assert abs(t.index('creditur')-record['position'])>abs(t.index('debet')-record['position'])


def test_capacity_and_noncrossing_are_distinct(adapter):
    t,p,s,_=arguments(PROBES[1])
    loose=Ownership(t,p,adapter,scopes=s,capacity=False,noncrossing=False)
    capacity=Ownership(t,p,adapter,scopes=s,capacity=True,noncrossing=False)
    joint=Ownership(t,p,adapter,scopes=s)
    assert all(len(r['possible_parents'])==2 for r in loose.records)
    assert all(len(r['possible_parents'])==2 for r in capacity.records)
    assert all(len(r['possible_parents'])==1 for r in joint.records)


def test_reporting_voice_is_lexically_constrained(adapter):
    t,p,s,_=arguments(PROBES[4]);o=Ownership(t,p,adapter,scopes=s)
    assert all(c['kind']!='passive_reporting' for choices in o.pool.values() for c in choices)


def test_conditional_owner_ambiguity_is_not_a_unique_bridge(adapter):
    t='creditur agricola puellam bonam capere debet quae cantat'.split();p=[0,5,7]
    base=infer(t,p,6,7,adapter,nonfinite=True,object_frames=True)
    assert base['status']=='unique_chain'
    owner=Ownership(t,p,adapter,scopes=((6,7),))
    result=filter_bridges(base,owner,6,7)
    assert result['status']=='ownership_ambiguous'
    assert result['chains'] and all(w['ownership']=='ambiguous' for w in result['chains'])


def test_homograph_can_remain_nominal_while_ownership_competes(adapter):
    t='creduntur sua praesentia fecundare quae spectant in parte secreta locare debemus'.split();p=[0,5,10];scopes=((4,5),)
    base=infer(t,p,4,5,adapter,scopes=scopes,nonfinite=True,object_frames=True)
    witness=next(w for w in base['chains'] if (w['antecedent'],w['via'],w['parent'])==(2,3,10))
    independent=Ownership(t,p,adapter,scopes=scopes,capacity=False,noncrossing=False)
    joint=Ownership(t,p,adapter,scopes=scopes)
    assert independent.assess(witness,4,5)=='ambiguous'
    assert joint.assess(witness,4,5)=='excluded'
    rec=next(r for r in joint.records if r['position']==2)
    assert rec['unresolved_possible'] and rec['selection_optional']
    assert next(r for r in joint.records if r['position']==9)['possible_parents']==[10]


def test_slot_conflict_does_not_contaminate_other_component(adapter):
    t,p,s,_=arguments(PROBES[-1]);o=Ownership(t,p,adapter,scopes=s)
    assert next(r for r in o.records if t[r['position']]=='fecundare')['status']=='unique'
    assert len(o.components)==2 and sum(not c['sat'] for c in o.components)==1


@pytest.mark.parametrize('arc1,arc2,expected',[
    ((0,4),(2,7),True),((4,0),(7,2),True),((0,7),(2,4),False),
    ((0,4),(4,7),False),((0,2),(4,7),False),
])
def test_crossing_geometry(arc1,arc2,expected):assert crosses(*arc1,*arc2)==expected


def test_finite_reading_is_shared_across_participles():
    from voynich_smt.grammar_diagnostic import LatinAdapter,MorphAnalysis
    def r(pos,**f):return MorphAnalysis(pos,tuple(sorted(f.items())))
    class Tiny(LatinAdapter):
        def __init__(self):pass
        def analyze(self,word):return lattice.get(word,())
    lattice={
        'one':(r('VPAR',Case='NOM',Gender='M',Number='S',Voice='ACTIVE'),),
        'two':(r('VPAR',Case='NOM',Gender='M',Number='P',Voice='ACTIVE'),),
        'singular':(r('N',Case='NOM',Gender='M',Number='S'),),
        'plural':(r('N',Case='NOM',Gender='M',Number='P'),),
        'finite':tuple(r('V',Mood='IND',Number=n,Person='3',Voice='ACTIVE') for n in ('S','P')),
    }
    o=Ownership(['singular','one','plural','two','finite'],[4],Tiny())
    c=o.components[0]
    assert c['sat']
    # Each participle can separately select this finite token, but they cannot
    # use singular and plural readings of it in the same ownership assignment.
    assert not o._query(c,z3.And(c['choice'][1]>=0,c['choice'][3]>=0))


def test_independent_boolean_checker_rejects_crossing_swap(adapter):
    from benchmarks.grammar_nonfinite_ownership_iteration16_validate import Independent
    t,p,scopes,_=arguments(PROBES[1]);model=Ownership(t,p,adapter,scopes=scopes)
    data=model.serializable();group=data['components'][0]['positions']
    checker=Independent(t,p,adapter,scopes,(),dict(capacity=True,noncrossing=True,reporting=True),data,group)
    assert not checker.query(checker.owner(t.index('laborare'),t.index('debet')),
        checker.owner(t.index('diligere'),t.index('creditur')))
    loose=Independent(t,p,adapter,scopes,(),dict(capacity=True,noncrossing=False,reporting=True),data,group)
    assert loose.query(loose.owner(t.index('laborare'),t.index('debet')),
        loose.owner(t.index('diligere'),t.index('creditur')))


def test_independent_checker_rejects_bad_reporting_license(adapter):
    from copy import deepcopy
    from benchmarks.grammar_nonfinite_ownership_iteration16_validate import Independent
    t,p,scopes,_=arguments(PROBES[1]);data=Ownership(t,p,adapter,scopes=scopes).serializable()
    data=deepcopy(data)
    candidate=next(c for c in data['candidates'][str(t.index('laborare'))] if c['kind']=='passive_reporting')
    candidate['kind']='modal'
    with pytest.raises(AssertionError):
        Independent(t,p,adapter,scopes,(),dict(capacity=True,noncrossing=True,reporting=True),data,data['components'][0]['positions'])


def test_unrestricted_unknown_owner_removes_coverage_entailment(adapter):
    from benchmarks.grammar_nonfinite_ownership_iteration16_validate import Independent
    t,p,scopes,_=arguments(PROBES[1]);data=Ownership(t,p,adapter,scopes=scopes).serializable()
    opts=dict(capacity=True,noncrossing=True,reporting=True)
    opened=Independent(t,p,adapter,scopes,(),opts,data,data['components'][0]['positions'],unknown_owner=True)
    a,b=t.index('laborare'),t.index('diligere')
    assert opened.query(opened.null[a],opened.null[b])
    assert opened.query(opened.owner(a,t.index('debet')),opened.null[b])
    closed=Independent(t,p,adapter,scopes,(),opts,data,data['components'][0]['positions'])
    assert not closed.query(closed.owner(a,t.index('debet')))
