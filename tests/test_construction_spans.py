import copy
import pytest
from benchmarks.grammar_construction_spans_iteration18 import OUT,load
from benchmarks.grammar_relative_constituents_iteration15_validate import FrozenAdapter,normalized
from benchmarks.grammar_construction_spans_iteration18_validate import check_witness
from voynich_smt.construction_spans import analyze

CASES=load(OUT/'controlled.json')
ADAPTER=FrozenAdapter(load(OUT/'morphology-lattice.json'))

@pytest.mark.parametrize('case',CASES,ids=[c['name'] for c in CASES])
def test_controlled(case):
    result=analyze(case['tokens'],case['predicates'],ADAPTER,case['model'])
    assert normalized(result)==case['result']
    assert result['parents']['typed']==case['expected']
    assert result['firm_claims']==[]
    for u in result['units']:
        if u['typed']['status']=='supported':
            check_witness(case['tokens'],case['predicates'],case['model']['units'][u['unit']],u['typed'],ADAPTER)

@pytest.mark.parametrize('name',['equal_distance_number','equal_distance_case'])
def test_morphology_separates_distance_tie(name):
    c=next(c for c in CASES if c['name']==name)
    nf=next(iter(c['expected']));pos=c['result']['parents']['pos'][nf]
    assert len(pos)==2 and abs(pos[0]-int(nf))==abs(pos[1]-int(nf))
    assert len(c['expected'][nf])==1


def test_dative_license_ablation():
    c=next(c for c in CASES if c['name']=='equal_distance_case')
    result=analyze(c['tokens'],c['predicates'],ADAPTER,c['model'],dative_frame=False)
    assert not any(result['parents']['typed'].values())


def test_witness_rejects_duplicate_token():
    c=next(c for c in CASES if c['name']=='perception_subject')
    u=next(u for u in c['result']['units'] if u['typed']['status']=='supported')
    corrupt=copy.deepcopy(u['typed']);corrupt['witness'].append(corrupt['witness'][0])
    with pytest.raises(AssertionError):check_witness(c['tokens'],c['predicates'],c['model']['units'][u['unit']],corrupt,ADAPTER)


def test_fragment_marks_unparsed_nested_edge():
    c=next(c for c in CASES if c['name']=='nested_not_a_complete_clause')
    assert any(c['tokens'][p]=='posse' for u in c['result']['units'] if u['typed']['status']=='supported' for p in u['typed']['open_nominal_or_nonfinite_edges'])
