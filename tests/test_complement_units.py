import pytest
import z3
from voynich_smt.complement_units import ComplementModel
from voynich_smt.relative_constituents import ConstituentAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from benchmarks.grammar_complement_units_iteration17 import PROBES,ARMS,arguments

@pytest.fixture(scope='module')
def adapter():return ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))

@pytest.mark.parametrize('probe',PROBES,ids=[p[0] for p in PROBES])
def test_fixed_contrasts(adapter,probe):
    t,p,requirements,expected=arguments(probe);assert len(p)>=3
    outputs=[ComplementModel(t,p,adapter,**opts).can_assign(requirements) for opts in ARMS.values()]
    assert tuple(outputs)==expected


def test_unknown_never_becomes_a_firm_claim(adapter):
    t,p,requirements,_=arguments(PROBES[0]);model=ComplementModel(t,p,adapter)
    assert model.can_assign(requirements) and model.query(*model.unknown.values())
    assert all(r['unknown_possible'] and r['firm_owner'] is None for r in model.serializable()['records'])


def test_shared_slot_requires_selected_coordination_unit(adapter):
    t,p,req,_=arguments(PROBES[5]);model=ComplementModel(t,p,adapter)
    paired=[model.selected[i] for i,u in enumerate(model.units) if len(u['members'])==2]
    assert paired and model.can_assign(req)
    assert not model.query(*[model.owner(nf,parent) for nf,parent in req],*[z3.Not(b) for b in paired])


def test_coordination_is_optional_for_unrelated_complements(adapter):
    t,p,req,_=arguments(PROBES[10]);model=ComplementModel(t,p,adapter)
    pairs=[model.selected[i] for i,u in enumerate(model.units) if len(u['members'])==2]
    assert pairs
    assert model.query(*[model.owner(nf,parent) for nf,parent in req],*[z3.Not(b) for b in pairs])


def test_known_finite_boundary_blocks_coordination(adapter):
    t,p,_,_=arguments(PROBES[8]);model=ComplementModel(t,p,adapter)
    assert not model.cues


def test_embedded_subject_number_is_independent_of_finite_governor(adapter):
    t='pueri currunt currere puerum uident puella ridet'.split();model=ComplementModel(t,[1,4,6],adapter)
    assert model.can_assign([(2,4)])
    candidate=next(c for c in model.pool[2] if c['parent']==4)
    assert candidate['readings'][3].get('Number')=='S'
    assert candidate['readings'][4].get('Number')=='P'


def test_perception_requires_one_accusative_reading(adapter):
    t,p,_,_=arguments(PROBES[2]);model=ComplementModel(t,p,adapter)
    index=next(i for i,u in enumerate(model.units) if u['kind']=='perception_aci')
    subject=model.units[index]['parts'][0]['embedded_subject']
    nominative=next(i for i,r in enumerate(adapter.analyze(t[subject])) if r.pos=='N' and r.get('Case')=='NOM')
    assert not model.query(model.selected[index],model.read[subject]==nominative)


def test_nominal_conjunction_is_not_an_infinitive_pair(adapter):
    t,p,_,_=arguments(PROBES[11]);assert not ComplementModel(t,p,adapter).cues


def test_normalized_negative_marker_requires_paired_prefix(adapter):
    t='pueri currunt conlocare ne c aperire debemus puella ridet'.split()
    model=ComplementModel(t,[1,6,8],adapter)
    assert model.can_assign([(2,6)]) and model.can_assign([(5,6)])
    assert not model.cues and not model.can_assign([(2,6),(5,6)])


def test_global_finite_reading_cannot_be_singular_and_plural():
    from voynich_smt.grammar_diagnostic import LatinAdapter,MorphAnalysis
    def r(pos,**f):return MorphAnalysis(pos,tuple(sorted(f.items())))
    lattice={'singular':(r('N',Case='NOM',Gender='M',Number='S'),),
        'plural':(r('N',Case='NOM',Gender='M',Number='P'),),
        'one':(r('VPAR',Case='NOM',Gender='M',Number='S',Voice='ACTIVE'),),
        'two':(r('VPAR',Case='NOM',Gender='M',Number='P',Voice='ACTIVE'),),
        'finite':tuple(r('V',Mood='IND',Number=n,Person='3',Voice='ACTIVE') for n in ('S','P'))}
    class Tiny(LatinAdapter):
        def __init__(self):pass
        def analyze(self,word):return lattice.get(word,())
    model=ComplementModel(['singular','one','plural','two','finite'],[4],Tiny())
    assert model.can_assign([(1,4)]) and model.can_assign([(3,4)])
    assert not model.can_assign([(1,4),(3,4)])


def test_independent_unit_cover_preserves_capacity(adapter):
    from benchmarks.grammar_complement_units_iteration17_validate import Exhaustive
    t,p,req,_=arguments(PROBES[5])
    for arm,expected in [('frames_open',False),('units_open',True)]:
        options=ARMS[arm];data=ComplementModel(t,p,adapter,**options).serializable()
        checker=Exhaustive(t,p,adapter,(),(),options,data)
        assert (checker.witness(req) is not None)==expected


def test_independent_checker_rejects_forged_marker(adapter):
    from copy import deepcopy
    from benchmarks.grammar_complement_units_iteration17_validate import Exhaustive
    t,p,_,_=arguments(PROBES[5]);options=ARMS['units_open']
    data=deepcopy(ComplementModel(t,p,adapter).serializable())
    pair=next(u for u in data['units'] if len(u['members'])==2)
    pair['cue']['marker_positions']=[pair['members'][0]]
    with pytest.raises(AssertionError):Exhaustive(t,p,adapter,(),(),options,data)
