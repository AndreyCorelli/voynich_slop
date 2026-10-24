from dataclasses import asdict
from benchmarks import shuffle_vocabulary_expansion as b
from voynich_smt.data.corpus import digest
from voynich_smt.solver.recovery import Recovery


def test_only_dictionary_changes_and_cached_pairs_match(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare();source=b.shuffles.prepare()
    assert len(p['cases'])==12
    for case in p['cases']:
        previous=next(c for c in source['controls'] if c['id']==case['original_control_id'])
        before=dict(previous['request']);after=dict(case['request']);before.pop('dictionary');after.pop('dictionary')
        assert digest(before)==digest(after)
        assert case['holdout']==previous['holdout'] and case['seed']==previous['seed']
        assert len(case['request']['dictionary']['words'])==256
        assert case['previous_64']['result']['status']=='UNSAT'


def test_training_request_only_unknown_unscored_resume_and_validate(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def spy(q):
        received.append(q);return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b,'recover_observed_codes',spy)
    r=b.run();p=b.prepare()
    assert len(received)==12
    assert [digest(asdict(q)) for q in received]==[digest(c['request']) for c in p['cases']]
    assert all(c['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in c for c in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==12
    b.validate()
