from dataclasses import asdict
import pytest
from benchmarks import natural_vocabulary_expansion as b
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
        assert digest(case['request']['dictionary']['words'][:64])==digest(original['request']['dictionary']['words'])
        assert case['holdout']==original['holdout']
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in a for a in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==16
    b.validate()


def test_reject_unmatched_baseline():
    source=b.baseline.prepare()
    with pytest.raises(ValueError,match='Unmatched completed'):
        b.build(source,{'complete':True,'prepared_sha256':'wrong'}, {})
