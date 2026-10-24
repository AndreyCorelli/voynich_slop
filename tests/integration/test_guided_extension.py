import importlib.util
from dataclasses import asdict
import json
from pathlib import Path
import pytest
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.data.corpus import write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.guided import recover_guided,fixed_word_conflicts


def setup(tmp_path):
    spec=importlib.util.spec_from_file_location('guided_extension',Path(__file__).parents[2]/'benchmarks/guided_extension.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    key=Encoder({'a':(('x',),),'b':(('y',),),'c':(('z',),)})
    suffix=HiddenRecoveryRequest(Text.from_string('x y'),Alphabet(tuple('abc')),Alphabet(tuple('xyz')),
        Bounds('verbose',2,1,3),WordDictionary.from_strings(('a','b','c','ac')),selection=HomophoneSelection('cycle'))
    result=recover_guided(suffix,key,('a','b','c'))
    assert result.status=='SAT' and result.verified
    from dataclasses import replace
    prefix=replace(suffix,ciphertext=Text.from_string('xy x y'))
    write_json(tmp_path/'suffix.json',asdict(suffix));write_json(tmp_path/'prefix.json',asdict(prefix))
    source={'conflict':{'status':'SAT','verified':True,'experiment_id':'suffix'},
        'prefix':{'status':'UNKNOWN','experiment_id':'prefix'},'source_conflict':{'start':1},
        'experiments':[{'id':'suffix','public_input':str(tmp_path/'suffix.json'),'result':asdict(result)},
                       {'id':'prefix','public_input':str(tmp_path/'prefix.json')}]}
    write_json(tmp_path/'source.json',source)
    return m,{'source_report':str(tmp_path/'source.json'),'timeout_ms':1000,'dictionary_encoding':'trie'},prefix,key


def test_release_runner_finds_and_verifies_the_whole_prefix(tmp_path,monkeypatch):
    m,cfg,prefix,key=setup(tmp_path)
    output=tmp_path/'result.json';artifacts=tmp_path/'artifacts'
    r=m.run(cfg,output,artifacts)
    assert r['complete'] and r['outcome']['status']=='SAT' and r['outcome']['verified']
    assert r['experiments'][0]['result']['status']=='UNSAT'
    assert r['experiments'][1]['result']['status']=='UNSAT'
    assert r['releases'][0]['basis']=='fixed decoding outside vocabulary'
    for row in r['experiments']:
        payload=json.loads(Path(row['public_input']).read_text())
        q,encoder,kwargs=m.load_input(payload)
        assert q.ciphertext==prefix.ciphertext and q.dictionary==prefix.dictionary
        assert q.bounds==prefix.bounds and q.selection==prefix.selection
        assert encoder.codebook==key.codebook
        assert recover_guided(q,encoder,**kwargs).status==row['result']['status']
        with pytest.raises(ValueError):HiddenRecoveryRequest.from_dict(payload)
    monkeypatch.setattr(m,'recover_guided',lambda *a,**k:pytest.fail('Completed resume should not solve'))
    assert m.run(cfg,output,artifacts,True)==json.loads(json.dumps(r))
    cfg['timeout_ms']=2000
    with pytest.raises(ValueError,match='identical'):m.run(cfg,output,artifacts,True)


def test_fixed_word_certificates_depend_on_all_code_owners(tmp_path):
    _,_,q,key=setup(tmp_path)
    conflicts=fixed_word_conflicts(q.ciphertext,key,('a','b'),q.dictionary)
    assert conflicts==[{'word_index':0,'decoded':['a','b'],'pinned_symbols':['a','b'],
                       'reason':'fixed decoding violates the language bounds'}]
    assert fixed_word_conflicts(q.ciphertext,key,('a',),q.dictionary)==[]
    assert recover_guided(q,key,('a',)).status=='SAT'


def test_unknown_is_retained_without_claiming_a_general_exclusion(tmp_path,monkeypatch):
    from voynich_smt.solver.recovery import Recovery
    m,cfg,_,_=setup(tmp_path)
    monkeypatch.setattr(m,'recover_guided',lambda *a,**k:Recovery('UNKNOWN',0,reason_unknown='test timeout'))
    r=m.run(cfg,tmp_path/'unknown.json',tmp_path/'artifacts')
    assert r['complete'] and r['outcome']['status']=='UNKNOWN'
    assert r['outcome']['pinned_symbols']==[] and r['outcome']['scope']=='unrestricted model'
    assert all(e['result']['status']=='UNKNOWN' for e in r['experiments'])
    assert all('fixed decoding' in release['basis'] or 'heuristic' in release['basis'] for release in r['releases'])
