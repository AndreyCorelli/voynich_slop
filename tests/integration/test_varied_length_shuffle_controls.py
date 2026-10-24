from dataclasses import asdict
import pytest
from benchmarks import varied_length_shuffle_controls as b
from voynich_smt.data.corpus import digest
from voynich_smt.solver.recovery import Recovery


def test_preparation_preserves_requested_invariants_and_freezes_seeds(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare()
    assert len(p['positives'])==6 and len(p['controls'])==12 and not p['unavailable']
    for case in p['controls']:
        positive=next(c for c in p['positives'] if c['id']==case['positive_id'])
        before=dict(positive['request']);after=dict(case['request']);before.pop('ciphertext');after.pop('ciphertext')
        assert before==after and case['request']['timeout_ms']==5000
        assert all(case['invariants'][k] for k in b.REQUIRED)
        assert case['request']['ciphertext']!=positive['request']['ciphertext']
    assert digest(b.prepare())==digest(p)


def test_only_training_request_supplied_unknown_unscored_and_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def spy(q):
        received.append(q);return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b,'recover_observed_codes',spy)
    r=b.run();p=b.prepare()
    assert len(received)==12
    assert [digest(asdict(q)) for q in received]==[digest(c['request']) for c in p['controls']]
    assert all(c['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in c for c in r['controls'])
    assert digest(b.run())==digest(r) and len(received)==12
    b.validate()


def test_bounded_generator_failure_recorded_without_extra_seed_selection(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    def unavailable(*args):raise ValueError('Unable to generate a changed collision-free word-type shuffle')
    monkeypatch.setattr(b,'typewise_shuffle',unavailable)
    p=b.prepare();assert not p['controls'] and len(p['unavailable'])==12
