import importlib.util
import json
from dataclasses import asdict
from pathlib import Path
import pytest
from voynich_smt.cipher.base import Bounds
from voynich_smt.data.corpus import write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import Recovery


def setup(tmp_path):
    spec=importlib.util.spec_from_file_location('l3_conflict',Path(__file__).parents[2]/'benchmarks/l3_conflict.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    request=HiddenRecoveryRequest(Text.from_string('xxxyyy yyyxxx xxxyyy'),Alphabet(tuple('abcd')),
        Alphabet(tuple('xyz')),Bounds('verbose',2,1,2),
        WordDictionary.from_strings(('ab','ba','aca','dad','bcd','abcd','cab','bb','dd','adc')),
        selection=HomophoneSelection('cycle'))
    write_json(tmp_path/'input.json',asdict(request))
    write_json(tmp_path/'scaling.json',{'experiments':[{'public_input':str(tmp_path/'input.json')}],
        'maximum_sample':{'record_indices':[10,11,12]}})
    write_json(tmp_path/'boundary.json',{'source_report':str(tmp_path/'scaling.json'),
        'conflict':{'start':1,'end':3,'shortest_unsat_suffix_proven':True}})
    config={'boundary_report':str(tmp_path/'boundary.json'),'synthetic_seeds':[7],
        'gate_timeout_ms':1000,'attempts':[{'dictionary_encoding':'flat','timeout_ms':1000},
                                        {'dictionary_encoding':'trie','timeout_ms':1000}]}
    return module,config,request


def test_l3_runner_preserves_model_and_separates_ground_truth(tmp_path,monkeypatch):
    m,cfg,base=setup(tmp_path)
    r=m.run(cfg,tmp_path/'result.json',tmp_path/'artifacts')
    assert r['complete'] and r['synthetic_gate']['passed']
    assert r['conflict']['status']=='SAT' and r['prefix']['status']=='SAT'
    assert r['source_conflict']['start']==1
    for e in r['experiments']:
        payload=json.loads(Path(e['public_input']).read_text())
        if e['mode']=='hidden':
            q=HiddenRecoveryRequest.from_dict(payload)
            assert 'plaintext' not in payload and 'encoder' not in payload
            assert q.bounds==Bounds('verbose',2,1,3)
            assert q.selection==base.selection
            if e['phase']=='observed':
                assert q.dictionary==base.dictionary
                assert q.plaintext_alphabet==base.plaintext_alphabet
                assert q.ciphertext_alphabet==base.ciphertext_alphabet
                assert e['source_record_indices'] in ([11,12],[10,11,12])
        if e['phase']=='synthetic':assert 3 in e['used_code_lengths']
    monkeypatch.setattr(HiddenRecoveryRequest,'solve',lambda q:pytest.fail('Completed resume must reuse results'))
    assert m.run(cfg,tmp_path/'result.json',tmp_path/'artifacts',True)==json.loads(json.dumps(r))


def test_unresolved_required_gate_stops_manuscript_checks(tmp_path,monkeypatch):
    m,cfg,_=setup(tmp_path)
    monkeypatch.setattr(m,'recover',lambda *a,**k:Recovery('UNKNOWN',0,reason_unknown='test timeout'))
    r=m.run(cfg,tmp_path/'result.json',tmp_path/'artifacts')
    assert r['complete'] and not r['synthetic_gate']['passed']
    assert all(e['phase']=='synthetic' for e in r['experiments'])
    assert 'prefix' not in r and 'conflict' not in r


def test_unknown_prefix_retries_encoding_without_changing_hypothesis(tmp_path,monkeypatch):
    m,cfg,base=setup(tmp_path)
    original=HiddenRecoveryRequest.solve
    def solve(q):
        if q.ciphertext==base.ciphertext:return Recovery('UNKNOWN',0,reason_unknown='test timeout')
        return original(q)
    monkeypatch.setattr(HiddenRecoveryRequest,'solve',solve)
    r=m.run(cfg,tmp_path/'result.json',tmp_path/'artifacts')
    assert r['conflict']['status']=='SAT' and r['prefix']['status']=='UNKNOWN'
    rows=[e for e in r['experiments'] if e['id'].startswith('prefix-')]
    assert [e['dictionary_encoding'] for e in rows]==['flat','trie']
    first,second=[json.loads(Path(e['public_input']).read_text()) for e in rows]
    first.pop('dictionary_encoding');second.pop('dictionary_encoding')
    assert first==second


@pytest.mark.parametrize('field,value',[('synthetic_seeds',[]),('synthetic_seeds',[True]),('gate_timeout_ms',0),('attempts',[])])
def test_invalid_configuration_rejected(tmp_path,field,value):
    m,cfg,_=setup(tmp_path);cfg[field]=value
    with pytest.raises(ValueError):m.validate(cfg)
