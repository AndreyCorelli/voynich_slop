from dataclasses import asdict
from benchmarks import oov_type_calibration as b
from voynich_smt.solver.recovery import Recovery
from voynich_smt.data.corpus import digest


def test_frozen_matched_arms_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);calls=[]
    def spy(q,budget):
        calls.append((digest(asdict(q)),budget));return Recovery('UNKNOWN',.01)
    monkeypatch.setattr(b,'recover_oov',spy);monkeypatch.setattr(b,'recover_oov_types',spy)
    r=b.run();p=b.prepare()
    assert len(calls)==24 and all(calls[i]==calls[i+1] for i in range(0,24,2))
    assert all(c['removed_occurrences']==2 and len(c['request']['dictionary']['words'])==63 for c in p['cases'])
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' for a in r['arms'])
    assert digest(b.run())==digest(r) and len(calls)==24
    b.validate()
