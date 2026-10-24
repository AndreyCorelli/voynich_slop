from benchmarks import one_oov_timeout_remaining as b
from voynich_smt.solver.recovery import Recovery
from voynich_smt.data.corpus import digest


def test_timeout_only_inputs_and_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def solve(q,budget):
        received.append((q,budget));return Recovery('UNKNOWN',.01)
    monkeypatch.setattr(b,'recover_oov',solve)
    r=b.run();p=b.prepare()
    assert len(received)==8 and [c['id'] for c in p['cases']]==list(b.PAIR)
    assert all(q.timeout_ms==60000 and budget==1 for q,budget in received)
    assert all(c['previous_5s']['result']['status']=='UNKNOWN' for c in p['cases'])
    assert digest(b.run())==digest(r) and len(received)==8
    b.validate()
