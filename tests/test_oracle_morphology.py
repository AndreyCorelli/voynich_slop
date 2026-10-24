import copy
import pytest
from benchmarks.grammar_oracle_morphology_iteration19 import OUT,EIGHTEEN,NINE,load,OverlayAdapter
from benchmarks.grammar_relative_constituents_iteration15_validate import FrozenAdapter

ADDITIONS=load(OUT/'oracle-readings.json')
LATTICE=load(EIGHTEEN/'morphology-lattice.json')

@pytest.mark.parametrize('addition',ADDITIONS,ids=[f"{a['stream']}:{a['position']}" for a in ADDITIONS])
def test_overlay_only_adds_absent_reading(addition):
    base=FrozenAdapter(LATTICE);adapter=OverlayAdapter(LATTICE,[addition])
    assert not base.analyze(addition['word'])
    assert len(adapter.analyze(addition['word']))==1
    for word in LATTICE:
        if word!=addition['word']:assert adapter.analyze(word)==base.analyze(word)
    assert set(dict(adapter.analyze(addition['word'])[0].features))=={'Case','Gender','Number'}
    assert 'head' not in addition and 'relation' not in addition and 'owner' not in addition

@pytest.mark.parametrize('key',['34:42','34:43','49:2'])
def test_each_recovered_reading_is_necessary(key):
    metrics=load(OUT/'evaluation.json')
    assert metrics['reference_scope/hidden']['typed']['reference_owner_retained']==16
    assert metrics['leave_one_out'][key]['reference_scope/hidden']['typed']['reference_owner_retained']==15

@pytest.mark.parametrize('key',['56:34','61:14'])
def test_morphology_does_not_solve_remaining_grammar(key):
    metrics=load(OUT/'evaluation.json')
    assert metrics['leave_one_out'][key]['reference_scope/hidden']['typed']['reference_owner_retained']==16
    stream=int(key.split(':')[0])
    audits=[a for a in load(OUT/'audit.json') if a['stream']==stream]
    assert audits and all(a['oracle_pos']==[a['reference_owner']] and not a['oracle_typed'] for a in audits)


def test_correct_owner_can_have_wrong_internal_role():
    case=next(a for a in load(OUT/'audit.json') if a['surface']=='fecundare')
    assert case['oracle_typed']==[case['reference_owner']]
    witness=next(e['result']['witness'] for e in case['evidence'] if e['result']['status']=='supported')
    role=next(s for s in witness if s.get('phrase',{}).get('head')==3)
    assert role['role']=='passive_instrument' and role['target']==0 # Source attaches it to fecundare (4).
