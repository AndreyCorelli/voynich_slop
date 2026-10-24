import copy
import pytest
from benchmarks.grammar_structure_preferences_iteration22 import OUT,TWENTYONE,SEVENTEEN,NINE,load,produce
from benchmarks.grammar_structure_preferences_iteration22_validate import validate_linear
from voynich_smt.structure_preferences import select,POLICIES,features,FAMILIES

RESULT=load(OUT/'evaluation.json')
CASES={c['id']:c for c in RESULT['cases'] if c['morphology']=='oracle_missing'}

@pytest.mark.parametrize('policy',POLICIES)
def test_ties_preserved_under_reversal(policy):
    for c in CASES.values():
        chosen=select(c['features'],policy);rev=select(list(reversed(c['features'])),policy)
        assert set(chosen)=={len(c['features'])-1-i for i in rev}

@pytest.mark.parametrize('policy',POLICIES)
def test_identical_candidates_cannot_be_separated(policy):
    vector=CASES['49:4->0']['features'][0]
    assert select([vector,copy.deepcopy(vector)],policy)==[0,1]


def test_frame_policy_resolves_three_and_abstains_on_object():
    counts=RESULT['summary']['oracle_missing']['policies']['construction_frame']
    assert counts['unique_correct']==3 and counts['unique_wrong']==0
    assert CASES['61:10,13->18']['selected']['construction_frame']==[3,9,15]

@pytest.mark.parametrize('policy,case',[('construction_matrix','49:4->0'),('construction_infinitive','58:38->35')])
def test_global_attachment_defaults_have_counterexamples(policy,case):
    assessment=CASES[case]['policies'][policy]['strict']
    assert assessment['unique'] and not assessment['unique_correct']


def test_nearest_distance_can_drop_reference():
    assert not CASES['61:10,13->18']['policies']['distance']['strict']['reference_available']


def test_oracle_readings_leave_attachment_ambiguity():
    assert {key:sum(CASES[key]['source_reading_labels']) for key in ('45:24->22','49:4->0','58:38->35','61:10,13->18')}=={'45:24->22':1,'49:4->0':2,'58:38->35':4,'61:10,13->18':9}
    assert RESULT['summary']['oracle_missing']['oracle_reading_policies']['all']['unique_correct']==1


def test_relaxed_equivalence_keeps_wrong_target_distinct():
    c=CASES['61:10,13->18']
    assert c['equivalent_labels'][3] and c['equivalent_labels'][15]
    assert not c['equivalent_labels'][9]
    assert sum(CASES['58:38->35']['equivalent_labels'])==2


def test_singleton_missing_reference_is_not_selectable():
    c=CASES['61:13->18']
    assert not c['reference_available'] and not any(c['strict_labels'])
    assert RESULT['summary']['oracle_missing']['ambiguous_without_reference']==['61:13->18']


def test_feature_collisions_are_real():
    c=CASES['61:10,13->18']
    assert [3,9] in c['feature_collisions']['frame']
    assert all(c['features'][3][name]==c['features'][9][name] for name in FAMILIES['frame'])
    assert c['features'][3]['dependency_distance']>c['features'][9]['dependency_distance']


def test_linear_fit_requires_positive_distance_weight():
    records=RESULT['feature_family_feasibility']['oracle_missing']
    assert records['frame']['status']=='unsat'
    assert records['frame_distance']['status']=='sat'
    assert records['frame_distance_nonpositive']['status']=='unsat'
    validate_linear(RESULT)


def test_annotation_metadata_does_not_enter_predictions():
    dev=load(NINE/'development-truth.json')
    stripped=[{'tokens':s['tokens']} for s in dev]
    assert produce(load(TWENTYONE/'predictions.json'),load(SEVENTEEN/'models.json'),stripped)==load(OUT/'predictions.json')


def test_surface_identity_does_not_enter_preference_features():
    rows=load(TWENTYONE/'predictions.json');models=load(SEVENTEEN/'models.json');dev=load(NINE/'development-truth.json')
    r=next(r for r in rows if r['stream']==61 and r['morphology']=='oracle_missing' and r['arm']=='participles_nisi' and r['mode']=='reference_scope' and r['boundaries']=='hidden')
    m=next(m['model'] for m in models if m['stream']==61 and m['arm']=='units_open' and m['mode']=='reference_scope' and m['boundaries']=='hidden')
    for u in r['result']['units']:
        for s in u['result'].get('structures',[]):
            unit=m['units'][u['unit']]
            assert features(dev[61]['tokens'],unit,s)==features(['zzz']*len(dev[61]['tokens']),unit,s)


def test_annotation_convention_can_hide_compatible_reading():
    audit=RESULT['annotation_convention_audit']
    assert len(audit)==6 and not any(any(a['strict_labels']) for a in audit)
    assert sum(any(a['relaxed_labels']) for a in audit)==2
    assert all(a['rewrites']==[{'position':43,'source_head':44,'modeled_head':42,'source_upos':'ADJ','modeled_pos':'N'}] for a in audit)
