from dataclasses import asdict
import json
import pytest
from benchmarks import training_diversity_indexed as b
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.recovery import Recovery


def test_solver_receives_request_only_without_lengths(monkeypatch):
    source,baseline,p=b.prepare();q=HiddenRecoveryRequest.from_dict(p['cases'][0]['request'])
    captured=[];sentinel=object()
    def spy(*args,**kwargs):captured.append((args,kwargs));return sentinel
    monkeypatch.setattr(b,'recover_observed_codes',spy)
    assert b.solve(q) is sentinel
    assert captured==[((q,),{})]


def test_matched_inputs_unknown_unscored_resume_and_validation(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def spy(q):
        received.append(q);return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b,'solve',spy)
    r=b.run();p=json.loads((tmp_path/'prepared.json').read_text())
    for q,case in zip(received,p['cases']):
        assert digest(asdict(q))==digest(case['request'])
        assert q.timeout_ms==5000 and len(q.ciphertext.words)==72
        assert not any(k in case for k in ('truth','revealed_lengths','holdout','holdout_plaintext'))
    assert all(row['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in row for row in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==2
    b.validate()


def test_changed_identity_rejects_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);b.prepare()
    path=tmp_path/'prepared.json';p=json.loads(path.read_text());p['identity']['source_sha256']='changed';path.write_text(json.dumps(p))
    with pytest.raises(ValueError,match='changed'):b.prepare()


def test_preparation_tracks_dictionary_implementation_and_prior_results(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    source,baseline,p=b.prepare()
    assert 'src/voynich_smt/language/dictionary.py' in p['identity']['code_sha256']
    old=json.loads(__import__('pathlib').Path('experiments/results/training-diversity-hidden/report.json').read_text())
    assert p['identity']['previous_hidden_report_sha256']==digest(old)
    assert all(c['previous_hidden']['status']=='UNKNOWN' for c in p['cases'])
    assert p['protocol']['environment']['z3']
