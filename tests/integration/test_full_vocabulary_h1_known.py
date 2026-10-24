import json

import pytest

from benchmarks import full_vocabulary_h1_known as b
from benchmarks.l3_conflict import verify
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text


def test_solver_receives_only_training_plaintext_and_public_cipher_model(monkeypatch):
    p=json.loads((b.SOURCE/'prepared.json').read_text())
    q=HiddenRecoveryRequest.from_dict(p['requests']['full'])
    plain=Text(tuple(tuple(w) for w in p['truth']['plaintext']['words']))
    captured=[];sentinel=object()
    def spy(*args,**kwargs):captured.append((args,kwargs));return sentinel
    monkeypatch.setattr(b,'_recover',spy)
    assert b.solve(plain,q) is sentinel
    args,kwargs=captured[0]
    assert args==(plain,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,q.timeout_ms)
    assert kwargs=={'representation':q.representation,'selection':q.selection,'codeword_domains':'observed'}


def test_known_plaintext_control_recovers_novel_words(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);r=b.run()
    p=json.loads((b.SOURCE/'prepared.json').read_text())
    verify(HiddenRecoveryRequest.from_dict(p['requests']['full']),r['result'])
    assert r['result']['status']=='SAT' and r['result']['verified']
    assert r['exact_words']==r['novel_exact_words']==3
    assert r['prediction']['seen_ciphertext_words']==0
    assert r['hidden_status']=='UNKNOWN'
    assert r['result']['plaintext']['words']==tuple(tuple(w) for w in p['truth']['plaintext']['words'])
    with pytest.raises(ValueError,match='preserve it'):b.run()


def test_unknown_is_unscored(tmp_path,monkeypatch):
    from voynich_smt.solver.recovery import Recovery
    monkeypatch.setattr(b,'OUT',tmp_path)
    monkeypatch.setattr(b,'solve',lambda plain,q:Recovery('UNKNOWN',0.01,reason_unknown='forced'))
    r=b.run()
    assert r['evaluation_status']=='NOT_EVALUATED_NO_SAT'
    assert 'prediction' not in r and 'exact_words' not in r
