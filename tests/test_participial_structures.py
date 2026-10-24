import copy
import pytest
from benchmarks.grammar_participial_structures_iteration21 import OUT,ARMS,load
from benchmarks.grammar_participial_structures_iteration21_validate import check_structure,flags
from benchmarks.grammar_oracle_morphology_iteration19 import OverlayAdapter
from voynich_smt.participial_structures import recognize

CASES={c['name']:c for c in load(OUT/'controlled.json')}
LATTICE=load(OUT/'morphology-lattice.json');ADAPTER=OverlayAdapter(LATTICE,[])


def entries(name,arm='participles_nisi',clausal=True):
    c=CASES[name]
    return [(c,c['model']['units'][u['unit']],u['result'],s) for u in c['results'][arm]['units'] for s in u['result'].get('structures',[]) if not clausal or any('clause' in seg for seg in s['witness'])]

@pytest.mark.parametrize('name',CASES)
def test_saved_witnesses(name):
    for arm in ARMS:
        for c,unit,result,s in entries(name,arm,False):check_structure(c['tokens'],c['predicates'],unit,result,s,ADAPTER,flags(arm))

@pytest.mark.parametrize('name',['number_mismatch','gender_mismatch','case_mismatch','no_participle','nisi_number_mismatch','nisi_finite_barrier','unknown_subject'])
def test_negative_clausal_structures(name):
    assert not entries(name)

@pytest.mark.parametrize('name',['subject_before_participle','participle_before_subject','source_defensis'])
def test_positive_clausal_structures(name):
    assert entries(name,'participles') and not entries(name,'baseline')


def test_nisi_requires_its_own_frame():
    assert not entries('nisi_subject_participle','participles')
    assert entries('nisi_subject_participle','participles_nisi')


def test_nisi_frame_works_without_noun_homograph():
    c,unit,_,_=entries('nisi_subject_participle')[0]
    lattice=copy.deepcopy(LATTICE);lattice['nisi']=[r for r in lattice['nisi'] if r['pos']=='CONJ']
    adapter=OverlayAdapter(lattice,[])
    result=recognize(c['tokens'],c['predicates'],adapter,unit,nisi_clause=True)
    assert result['status']=='supported' and any('clause' in seg for s in result['structures'] for seg in s['witness'])


def test_participle_wildcard_is_bound_to_subject():
    e=entries('nisi_subject_participle')
    clauses=[seg['clause'] for _,_,_,s in e for seg in s['witness'] if 'clause' in seg]
    assert all(cl['agreement']=={'Case':'ABL','Gender':'M','Number':'S'} for cl in clauses)


def test_independent_checker_rejects_incorrect_binding():
    c,unit,r,s=entries('subject_before_participle')[0];bad=copy.deepcopy(s)
    next(seg['clause'] for seg in bad['witness'] if 'clause' in seg)['agreement']['Number']='P'
    with pytest.raises(AssertionError):check_structure(c['tokens'],c['predicates'],unit,r,bad,ADAPTER,flags('participles_nisi'))


def test_independent_checker_rejects_internal_dependency_corruption():
    c,unit,r,s=entries('subject_before_participle')[0];bad=copy.deepcopy(s)
    bad['links']=[l for l in bad['links'] if l[2]!='participial_subject']
    with pytest.raises(AssertionError):check_structure(c['tokens'],c['predicates'],unit,r,bad,ADAPTER,flags('participles_nisi'))


def test_real_constructions_are_available_and_unresolved():
    audits=load(OUT/'audit.json')
    for stream,members,n in [(58,[38],8),(61,[10,13],27)]:
        a=next(a for a in audits if a['stream']==stream and a['members']==members and a['morphology']=='oracle_missing' and a['arm']=='participles_nisi')
        assert len(a['matches'])==n and sum(a['part_matches'])==1
        assert a['result']['attachment_status']=='unresolved'
    a=next(a for a in audits if a['stream']==61 and a['members']==[10,13] and a['morphology']=='oracle_missing' and a['arm']=='participles')
    assert not any(a['matches'])


def test_truncation_remains_unresolved():
    c,unit,_,_=entries('subject_before_participle')[0]
    r=recognize(c['tokens'],c['predicates'],ADAPTER,unit,limit=1)
    assert r['status']=='truncated' and not r['complete_enumeration'] and r['attachment_status']=='unresolved'
