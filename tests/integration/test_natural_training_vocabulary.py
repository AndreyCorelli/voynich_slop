from dataclasses import asdict
import pytest
from benchmarks import natural_training_vocabulary as b
from voynich_smt.data.corpus import digest
from voynich_smt.solver.recovery import Recovery


def test_dictionary_only_inputs_and_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def solve(q):
        received.append(q)
        return Recovery('UNKNOWN',.01,reason_unknown='forced')
    monkeypatch.setattr(b,'recover_observed_codes',solve)
    r=b.run();p=b.prepare()
    assert len(received)==16
    source=b.baseline.prepare()
    for q,case,original in zip(received,p['cases'],source['cases']):
        assert q.timeout_ms==5000 and len(q.dictionary.words)==256
        before=dict(original['request']);after=asdict(q)
        before.pop('dictionary');after.pop('dictionary')
        assert digest(before)==digest(after)
        training=sorted(set(tuple(w) for w in original['truth']['plaintext']['words'])) if original['kind']=='positive' else sorted(set(tuple(w) for w in source['passages'][case['passage_id']]['plaintext']['words']))
        assert digest(case['request']['dictionary']['words'][:len(training)])==digest(training)
        assert case['holdout']==original['holdout']
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in a for a in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==16
    b.validate()


def test_reject_unmatched_baseline():
    source=b.baseline.prepare()
    with pytest.raises(ValueError,match='Unmatched completed'):
        b.build(source,{'complete':True,'prepared_sha256':'wrong'}, {})


def test_dictionary_does_not_reserve_holdout():
    from copy import deepcopy
    import json
    source=b.baseline.prepare()
    previous=json.loads((b.baseline.OUT/'report.json').read_text())
    records,_,_=b.baseline.load_sources()
    dictionaries,_,_=b.build(source,previous,records)
    changed=deepcopy(source)
    for passage in changed['passages'].values():
        passage['holdout_plaintext']={'words':[['unreserved']]}
        passage['dictionary']={'words':[['unreserved']]}
    # Build checks provenance identity; update the synthetic fixture's paired hash.
    previous=dict(previous,prepared_sha256=digest(changed))
    changed_dictionaries,_,_=b.build(changed,previous,records)
    assert digest(dictionaries)==digest(changed_dictionaries)
