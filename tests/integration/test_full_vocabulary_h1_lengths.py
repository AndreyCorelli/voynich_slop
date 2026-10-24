import json

import pytest

from benchmarks import full_vocabulary_h1_lengths as b
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.recovery import Recovery


def test_solver_receives_lengths_and_dictionary_but_no_plaintext(monkeypatch):
    p=json.loads((b.SOURCE/'prepared.json').read_text())
    q=HiddenRecoveryRequest.from_dict(p['requests']['full'])
    lengths=tuple(map(len,p['truth']['plaintext']['words']))
    captured=[];sentinel=object()
    def spy(*args,**kwargs):captured.append((args,kwargs));return sentinel
    monkeypatch.setattr(b,'_recover',spy)
    assert b.solve(lengths,q) is sentinel
    args,kwargs=captured[0]
    assert args==(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,q.timeout_ms)
    assert kwargs['dictionary']==q.dictionary
    assert kwargs['known_word_lengths']==lengths
    assert 'known_segmentation' not in kwargs and 'guidance' not in kwargs
    assert kwargs['codeword_domains']=='observed'


def test_unknown_is_unscored_and_protocol_only_reveals_counts(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    monkeypatch.setattr(b,'solve',lambda lengths,q:Recovery('UNKNOWN',0.01,reason_unknown='forced'))
    r=b.run()
    p=json.loads((b.SOURCE/'prepared.json').read_text())
    assert tuple(r['protocol']['revealed_word_lengths'])==tuple(map(len,p['truth']['plaintext']['words']))
    assert 'revealed_plaintext' not in r['protocol']
    assert r['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in r
    with pytest.raises(ValueError,match='preserve it'):b.run()


def test_invalid_word_lengths_rejected_by_solver():
    p=json.loads((b.SOURCE/'prepared.json').read_text())
    q=HiddenRecoveryRequest.from_dict(p['requests']['full'])
    with pytest.raises(ValueError,match='Invalid plaintext word lengths'):
        b.solve((0,)*len(q.ciphertext.words),q)
