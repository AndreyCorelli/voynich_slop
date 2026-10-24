import importlib.util
import json
from dataclasses import asdict
from pathlib import Path

import pytest
from voynich_smt.data.corpus import write_json
from voynich_smt.solver.recovery import Recovery
from test_diagnostics import request


def module():
    spec=importlib.util.spec_from_file_location('unsat_boundary',Path(__file__).parents[2]/'benchmarks/unsat_boundary.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def source(tmp_path):
    q=request('a a a x y a')
    path=tmp_path/'input.json';write_json(path,asdict(q))
    path3=tmp_path/'three.json'
    from dataclasses import replace
    from voynich_smt.models.text import Text
    short=replace(q,ciphertext=Text(q.ciphertext.words[:3]))
    write_json(path3,asdict(short))
    report={'fixed_model':{},'maximum_sample':{'record_indices':list(range(6))},
        'experiments':[{'word_count':3,'public_input':str(path3),'result':asdict(short.solve())},
                       {'word_count':6,'public_input':str(path),'result':asdict(q.solve())}]}
    p=tmp_path/'source.json';write_json(p,report)
    return p


def test_certified_prefix_and_shortest_contiguous_suffix(tmp_path,monkeypatch):
    m=module();s=source(tmp_path);o=tmp_path/'result.json';a=tmp_path/'artifacts'
    r=m.run(s,o,a,(1000,))
    assert r['prefix']=={'largest_verified_sat':3,'smallest_proved_unsat':4,
                         'minimality_proven':True,'unresolved_sizes':[]}
    assert r['conflict']['start']==1 and r['conflict']['end']==4
    assert r['conflict']['shortest_unsat_suffix_proven']
    assert [e['result']['status'] for e in r['relaxations']]==['SAT','UNSAT','UNSAT','UNSAT']
    from voynich_smt.experiments.hidden import HiddenRecoveryRequest
    monkeypatch.setattr(HiddenRecoveryRequest,'solve',lambda q:pytest.fail('Completed resume should not solve'))
    assert m.run(s,o,a,(1000,),True)==json.loads(json.dumps(r))


def test_unknown_never_moves_the_certified_bracket(tmp_path,monkeypatch):
    m=module();s=source(tmp_path)
    from voynich_smt.experiments.hidden import HiddenRecoveryRequest
    original=HiddenRecoveryRequest.solve
    def solve(q):
        if 3<len(q.ciphertext.words)<6:return Recovery('UNKNOWN',0,reason_unknown='test timeout')
        return original(q)
    monkeypatch.setattr(HiddenRecoveryRequest,'solve',solve)
    r=m.run(s,tmp_path/'result.json',tmp_path/'artifacts',(1000,))
    assert r['complete'] and not r['prefix']['minimality_proven']
    assert r['prefix']['largest_verified_sat']==3 and r['prefix']['smallest_proved_unsat']==6
    assert sorted(r['prefix']['unresolved_sizes'])==[4,5]


def test_observation_reduction_certifies_each_needed_word(tmp_path):
    spec=importlib.util.spec_from_file_location('observation_core',Path(__file__).parents[2]/'benchmarks/observation_core.py')
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    s=source(tmp_path)
    boundary=module().run(s,tmp_path/'boundary.json',tmp_path/'inputs',(1000,))
    r=core.run(tmp_path/'boundary.json',tmp_path/'core.json',tmp_path/'masks',1000)
    assert r['complete'] and r['deletion_minimal_proven']
    assert r['retained_word_indices']==[1,3]
    assert r['experiments'][0]['result']['status']=='UNSAT'
    for row in r['experiments']:
        payload=json.loads(Path(row['mask_input']).read_text())
        assert len(payload['request']['ciphertext']['words'])==4
        assert payload['observed_word_indices']==row['observed_word_indices']
        assert 'cycle context retained' in payload['semantics']
