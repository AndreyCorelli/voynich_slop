import importlib.util
import json
from pathlib import Path

import pytest

from voynich_smt.data.corpus import Corpus
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def module():
    spec = importlib.util.spec_from_file_location('latin_frontier', Path(__file__).parents[2]/'benchmarks/latin_frontier.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def config(tmp_path):
    latin = Corpus('latin', {'sha256':'latin'}, {'alphabet':'ab'},
                   tuple({'tokens':list(w)} for w in ['a','aa','ab','ba','a','aa','ab','ba']))
    voynich = Corpus('voynich-eva', {'sha256':'eva'}, {},
                    ({'tokens':['x','y'],'folio':'f1r'}, {'tokens':['y','z'],'folio':'f1r'}))
    latin.save(tmp_path/'latin.json'); voynich.save(tmp_path/'eva.json')
    return {'latin':str(tmp_path/'latin.json'),'voynich':str(tmp_path/'eva.json'),
            'sample':{'words':2,'folio':'f1r'},'synthetic_seeds':[7,17],
            'control_seed':7,'controls':['frequency-shuffle'],'timeout_ms':1000,
            'selection_policies':[{'mode':'free','reset':'text'},{'mode':'cycle','reset':'text'}],
            'stages':[{'name':'small','vocabulary_size':2,'max_homophones':1,'max_code_length':2},
                      {'name':'all','vocabulary_size':'all','max_homophones':1,'max_code_length':2},
                      {'name':'h2','vocabulary_size':'all','max_homophones':2,'max_code_length':2}]}


def test_frontier_public_replay_pairing_relaxations_and_resume(tmp_path, monkeypatch):
    runner = module()
    cfg = config(tmp_path)
    output, artifacts = tmp_path/'results.json', tmp_path/'artifacts'
    first = runner.run(cfg,output,artifacts,['small'])
    assert first['complete'] and len(first['stages']) == 1
    assert first['selected_stage_names'] == ['small']
    runner.run(cfg,output,artifacts,resume=True)
    report = json.loads(output.read_text())
    assert report['complete'] and len(report['stages']) == 3
    for stage in report['stages']:
        assert all(p['synthetic_gate_passed'] for p in stage['policies'])
        a, b = stage['policies']
        assert [e['ciphertext_sha256'] for e in a['experiments']] == [e['ciphertext_sha256'] for e in b['experiments']]
        for policy in stage['policies']:
            for experiment in policy['experiments']:
                request = HiddenRecoveryRequest.from_dict(json.loads(Path(experiment['public_input']).read_text()))
                assert request.selection.mode == policy['selection']['mode']
                assert 'plaintext' not in json.loads(Path(experiment['public_input']).read_text())
    # Resuming a completed run must preserve all checkpoints without solving again.
    def forbidden(*args,**kwargs):
        raise AssertionError('Completed checkpoint was solved again')
    with monkeypatch.context() as patch:
        patch.setattr(runner.HiddenRecoveryRequest, 'solve', forbidden)
        assert runner.run(cfg,output,artifacts,resume=True)['stages'] == report['stages']


def test_resume_rejects_changed_assumptions(tmp_path):
    runner = module(); cfg = config(tmp_path)
    output = tmp_path/'report.json'
    runner.run(cfg,output,tmp_path/'artifacts',['small'])
    cfg['timeout_ms'] = 2000
    with pytest.raises(ValueError,match='identical'):
        runner.run(cfg,output,tmp_path/'artifacts',resume=True)


@pytest.mark.parametrize('change', ['two-dimensions','narrowing','bad-policy','duplicate-seeds','bad-control'])
def test_frontier_rejects_invalid_comparisons(tmp_path,change):
    runner = module(); cfg = config(tmp_path)
    if change=='two-dimensions':
        cfg['stages'][1]['max_homophones']=2
    elif change=='narrowing':
        cfg['stages'][1]['vocabulary_size']=1
    elif change=='bad-policy':
        cfg['selection_policies'][0]['mode']='random'
    elif change=='duplicate-seeds':
        cfg['synthetic_seeds']=[7,7]
    else:
        cfg['controls']=['unknown']
    with pytest.raises(ValueError):
        runner.validate(cfg)


def test_unknown_synthetic_results_never_pass_gate(tmp_path,monkeypatch):
    from voynich_smt.solver.recovery import Recovery
    runner = module(); cfg = config(tmp_path)
    monkeypatch.setattr(HiddenRecoveryRequest,'solve',lambda request:
                        Recovery('UNKNOWN',0.01,reason_unknown='timeout',capacity={'construction_seconds':0.0}))
    report = runner.run(cfg,tmp_path/'unknown.json',tmp_path/'artifacts',['small'])
    assert report['complete']
    assert all(not p['synthetic_gate_passed'] for p in report['stages'][0]['policies'])
    assert all(e['result']['reason_unknown']=='timeout' and e['result']['plaintext'] is None
               for p in report['stages'][0]['policies'] for e in p['experiments'])


def test_single_letter_filter_is_explicit(tmp_path):
    runner = module(); cfg = config(tmp_path)
    cfg['single_letter_words']=[]
    report = runner.run(cfg,tmp_path/'filtered.json',tmp_path/'artifacts',['small'])
    assert report['assumptions']['single_letter_words']==[]
    for policy in report['stages'][0]['policies']:
        for experiment in policy['experiments']:
            words=json.loads(Path(experiment['public_input']).read_text())['dictionary']['words']
            assert len(words)==2 and all(len(w)>1 for w in words)


def test_broader_timeout_can_inherit_verified_witness(tmp_path):
    from dataclasses import asdict
    from voynich_smt.cipher.base import Bounds, Encoder
    from voynich_smt.data.corpus import digest, write_json
    from voynich_smt.language.dictionary import WordDictionary
    from voynich_smt.models.alphabet import Alphabet
    from voynich_smt.models.settings import HomophoneSelection
    from voynich_smt.models.text import Text
    from voynich_smt.solver.recovery import Recovery
    runner=module()
    request=HiddenRecoveryRequest(Text.from_string('xy'),Alphabet(tuple('ab')),Alphabet(tuple('xy')),
            Bounds('verbose',2,1,2),WordDictionary.from_strings(('ab',)),selection=HomophoneSelection('cycle'))
    path=tmp_path/'broader.json';write_json(path,asdict(request))
    old=asdict(Recovery('SAT',0.01,encoder=Encoder({'a':(('x',),),'b':(('y',),)}),
                        plaintext=Text.from_string('ab'),choices=(0,0),verified=True))
    unknown=asdict(Recovery('UNKNOWN',1,reason_unknown='timeout'))
    shared={'dataset':'voynich','ciphertext_sha256':digest(asdict(request.ciphertext)),'public_input':str(path)}
    policy=asdict(request.selection)
    report={'stages':[{'name':'narrow','policies':[{'selection':policy,'experiments':[{**shared,'result':old}]}]},
                      {'name':'broad','policies':[{'selection':policy,'experiments':[{**shared,'result':unknown}]}]}]}
    runner.certify_existing_witnesses(report)
    broad=report['stages'][1]['policies'][0]['experiments'][0]
    assert broad['result']['status']=='UNKNOWN' and broad['result']['plaintext'] is None
    assert broad['inherited_feasibility']['status']=='SAT' and broad['inherited_feasibility']['verified']
    broad['result']['status']='UNSAT'
    with pytest.raises(RuntimeError,match='conflicts'):
        runner.certify_existing_witnesses(report)


def test_text_cycle_rejects_skipped_source_words(tmp_path):
    runner=module();cfg=config(tmp_path)
    c=Corpus.load(cfg['voynich'])
    gapped=Corpus(c.kind,c.source,c.normalization,(c.records[0],{'tokens':[],'folio':'f1r'},c.records[1]))
    gapped.save(cfg['voynich'])
    with pytest.raises(ValueError,match='uninterrupted'):
        runner.run(cfg,tmp_path/'report.json',tmp_path/'artifacts')
