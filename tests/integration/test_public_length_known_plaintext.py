import json
from dataclasses import asdict
from benchmarks import public_length_known_plaintext as b
from voynich_smt.solver.recovery import Recovery


def test_only_training_plaintext_and_original_request_supplied(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def spy(plain,q):
        received.append((plain,q))
        return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b,'solve',spy)
    r=b.run()
    p=json.loads((b.SOURCE/'prepared.json').read_text())
    for (plain,q),case_id in zip(received,b.CASE_IDS):
        case=next(c for c in p['cases'] if c['id']==case_id)
        assert asdict(plain)=={'words':tuple(tuple(w) for w in case['truth']['plaintext']['words'])}
        assert json.loads(json.dumps(asdict(q)))==case['request']
        assert q.timeout_ms==5000
    assert all(row['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in row for row in r['cases'])
    b.run()
    assert len(received)==4


def test_matched_oracle_fits_predict_all_novel_words(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    r=b.run()
    assert all(row['result']['status']=='SAT' and row['result']['verified'] for row in r['cases'])
    assert [row['hidden_exact_words'] for row in r['cases']]==[0,0,0,1]
    assert all(row['exact_words']==3 and row['prediction']['seen_ciphertext_words']==0 for row in r['cases'])
    b.validate()
    assert json.loads((tmp_path/'validation.json').read_text())['verified']


def test_changed_source_identity_rejects_resume(tmp_path,monkeypatch):
    import pytest
    monkeypatch.setattr(b,'OUT',tmp_path)
    b.prepare()
    path=tmp_path/'protocol.json';p=json.loads(path.read_text())
    p['identity']['source_sha256']='changed';path.write_text(json.dumps(p))
    with pytest.raises(ValueError,match='changed'):b.prepare()
