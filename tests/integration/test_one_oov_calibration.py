from dataclasses import asdict
from copy import deepcopy
import pytest
from benchmarks import one_oov_calibration as b
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.recovery import Recovery


def test_frozen_public_inputs_resume_and_validation(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def solve(q,budget):
        received.append((q,budget));return Recovery('UNKNOWN',.01,reason_unknown='forced')
    monkeypatch.setattr(b,'recover_oov',solve)
    r=b.run();p=b.prepare()
    assert len(received)==16
    for (q,budget),case in zip(received,p['cases']):
        assert budget==1 and q.timeout_ms==5000
        assert digest(asdict(q))==digest(case['request'])
        assert case['removed_type_count']==1
        assert len(q.dictionary.words)==255
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' for a in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==16
    b.validate()


def test_independent_verifier_rejects_excess_oov():
    p=b.prepare();case=next(c for c in p['cases'] if c['kind']=='positive')
    q=HiddenRecoveryRequest.from_dict(case['request']);b.verify_oov(q,case['truth'])
    from dataclasses import replace
    from voynich_smt.language.dictionary import WordDictionary
    words=set(map(tuple,case['truth']['plaintext']['words']))
    q=replace(q,dictionary=WordDictionary(tuple(w for w in q.dictionary.words if w not in words)))
    with pytest.raises(RuntimeError,match='budget exceeded'):b.verify_oov(q,case['truth'])
