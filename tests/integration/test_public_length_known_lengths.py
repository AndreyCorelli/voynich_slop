import json
from dataclasses import asdict
import pytest
from benchmarks import public_length_known_lengths as b
from voynich_smt.data.corpus import digest
from voynich_smt.solver.recovery import Recovery


def test_only_training_lengths_and_unchanged_request_passed(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def spy(lengths,q):
        received.append((lengths,q));return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b,'solve',spy)
    r=b.run();p=json.loads((b.SOURCE/'prepared.json').read_text())
    for (lengths,q),case_id in zip(received,b.CASE_IDS):
        case=next(c for c in p['cases'] if c['id']==case_id)
        assert lengths==tuple(map(len,case['truth']['plaintext']['words']))
        assert digest(asdict(q))==digest(case['request']) and q.timeout_ms==5000
    protocol=json.loads((tmp_path/'protocol.json').read_text())
    assert 'revealed_plaintexts' not in protocol
    assert all(row['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in row for row in r['cases'])
    assert all(row['known_word_exact_words']==3 for row in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==4
    b.validate()


def test_changed_protocol_identity_rejects_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);b.prepare()
    path=tmp_path/'protocol.json';p=json.loads(path.read_text());p['identity']['source_sha256']='changed';path.write_text(json.dumps(p))
    with pytest.raises(ValueError,match='changed'):b.prepare()
