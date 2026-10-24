import copy
import pytest
from benchmarks.grammar_argument_structures_iteration20 import OUT,ARMS,load
from benchmarks.grammar_argument_structures_iteration20_validate import check_structure
from benchmarks.grammar_oracle_morphology_iteration19 import OverlayAdapter
from voynich_smt.argument_structures import recognize

CASES={c['name']:c for c in load(OUT/'controlled.json')}
LATTICE=load(OUT/'morphology-lattice.json')
ADAPTER=OverlayAdapter(LATTICE,[])


def structures(name,arm='joint',paired=False):
    c=CASES[name]
    return [(c,c['model']['units'][u['unit']],u['result'],s) for u in c['results'][arm]['units'] if not paired or len(c['model']['units'][u['unit']]['members'])==2 for s in u['result'].get('structures',[])]

@pytest.mark.parametrize('name',CASES)
def test_all_control_witnesses(name):
    c=CASES[name]
    for arm in ARMS:
        for _,unit,result,s in structures(name,arm):check_structure(c['tokens'],c['predicates'],unit,result,s,ADAPTER,ARMS[arm])

@pytest.mark.parametrize('name',['wrong_object_cases','missing_object_coordinator','bad_object_modifier','wrong_segment_two_objects','object_not_intransitive'])
def test_negative_argument_covers(name):
    assert all(not any(r['parents'].values()) for r in CASES[name]['results'].values())


def test_coordination_and_valency_are_separate():
    c=CASES['correlative_objects']
    assert not any(c['results']['coordination']['parents'].values())
    entries=structures('correlative_objects','coordination_frame')
    assert entries
    groups=entries[0][3]['groups']
    assert groups==[{'role':'object','heads':[4,6],'targets':[7]}]
    assert not any(CASES['object_coordination']['results']['attachment']['parents'].values())


def test_shared_object_stays_ambiguous():
    entries=structures('shared_or_single_object',paired=True)
    groups={tuple(g['targets']) for _,_,_,s in entries for g in s['groups'] if g['role']=='object'}
    assert groups=={(2,),(4,),(2,4)}
    assert all(r['attachment_status']=='unresolved' for _,_,r,_ in entries)


def test_separate_objects_use_separate_slots():
    entries=structures('separate_objects',paired=True)
    assert entries
    assert entries[0][3]['groups']==[{'role':'object','heads':[3],'targets':[4]},{'role':'object','heads':[6],'targets':[7]}]


def test_ablative_does_not_force_correct_attachment():
    entries=structures('ambiguous_ablative_attachment')
    assert {tuple(g['targets']) for _,_,_,s in entries for g in s['groups']}=={(2,),(5,)}
    assert all(r['attachment_status']=='unresolved' for _,_,r,_ in entries)


def test_nominal_homographs_explain_mismatch_survival():
    # A plural bonis adjective cannot agree with singular praesentia, but bonis
    # also has noun readings. Preserve that lexical ambiguity, then isolate it.
    entries=structures('ablative_modifier_mismatch');assert entries
    assert all(not any(set(p['analyses'])=={'3','4'} for seg in s['witness'] for p in seg.get('phrases',[])) for _,_,_,s in entries)
    lattice=copy.deepcopy(LATTICE);lattice['bonis']=[r for r in lattice['bonis'] if r['pos']=='ADJ']
    c,unit,_,_=entries[0]
    result=recognize(c['tokens'],c['predicates'],OverlayAdapter(lattice,[]),unit,**ARMS['joint'])
    assert result['status']=='no_role_cover'


def test_truncation_cannot_claim_unique_attachment():
    c,unit,_,_=structures('ambiguous_ablative_attachment')[0]
    r=recognize(c['tokens'],c['predicates'],ADAPTER,unit,limit=1)
    assert r['status']=='truncated' and not r['complete_enumeration'] and r['attachment_status']=='unresolved'


def test_validator_rejects_argument_reuse():
    c,unit,r,s=structures('object_coordination')[0];bad=copy.deepcopy(s)
    bad['witness'].append(next(seg for seg in bad['witness'] if 'phrases' in seg))
    with pytest.raises(AssertionError):check_structure(c['tokens'],c['predicates'],unit,r,bad,ADAPTER,ARMS['joint'])


def test_correct_owner_has_both_correct_and_wrong_local_attachment():
    audits=load(OUT/'audit.json')
    a=next(a for a in audits if a['stream']==49 and a['members']==[4] and a['arm']=='joint' and a['morphology']=='oracle_missing')
    assert a['matches']==[False,True]
    assert a['result']['attachment_status']=='unresolved'


def test_broad_ablative_is_not_participial_structure_recovery():
    audits=load(OUT/'audit.json')
    for stream in (58,61):
        examples=[a for a in audits if a['stream']==stream and a['arm']=='joint' and a['morphology']=='oracle_missing']
        assert examples and all(not any(a['links_and_pos_matches']) for a in examples)
