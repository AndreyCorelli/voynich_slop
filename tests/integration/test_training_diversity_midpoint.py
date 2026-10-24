import json
from dataclasses import asdict
from benchmarks import training_diversity_midpoint as b
from voynich_smt.data.corpus import digest


def test_public_schedule_receives_only_request(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def proposals(q):
        received.append(q)
        yield (1,)*len(q.ciphertext.words)
    monkeypatch.setattr(b.midpoint_grouped,'proposals',proposals)
    source,p=b.prepare()
    assert len(received)==2
    for q,case in zip(received,p['cases']):
        assert digest(asdict(q))==digest(case['request'])
        assert q.timeout_ms==5000 and len(q.ciphertext.words)==72
        assert not any(k in case for k in ('truth','revealed_lengths','holdout','holdout_plaintext'))
    b.prepare();assert len(received)==2


def test_non_sat_search_unscored_and_checkpointed(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    monkeypatch.setattr(b.midpoint_grouped,'proposals',lambda q:iter([(1,)*len(q.ciphertext.words)]))
    calls=[]
    def search(q,vectors):
        calls.append((q,vectors))
        return {'status':'UNKNOWN','attempts':[],'remaining_solver_budget_ms':5000,'solver_seconds':0}
    monkeypatch.setattr(b.midpoint,'search',search)
    r=b.run()
    assert len(calls)==2
    assert all(c['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in c for c in r['cases'])
    assert digest(b.run())==digest(r) and len(calls)==2
    b.validate()


def test_grouped_order_exactly_matches_original_cartesian_filter():
    from types import SimpleNamespace
    from voynich_smt.solver.length_search import ranked_vectors
    words=(tuple('xxxx'),tuple('xxxx'),tuple('xxxxxx'))
    domains=((1,2,3),(1,2,3),(1,2,3,4))
    relations=(SimpleNamespace(prefix='equal',left=0,right=1),SimpleNamespace(prefix='left',left=0,right=2))
    ranked=tuple(tuple(sorted(d,key=lambda n:(abs(n*4-2*len(w)),n))) for d,w in zip(domains,words))
    original=[v for v in ranked_vectors(ranked) if v[0]==v[1] and v[0]<v[2]]
    assert list(b.midpoint_grouped.vectors(domains,words,4,relations))==original


def test_schedule_preparation_resumes_completed_case(tmp_path,monkeypatch):
    import pytest
    monkeypatch.setattr(b,'OUT',tmp_path);calls=[]
    def proposals(q):
        calls.append(q)
        if len(calls)==2:raise RuntimeError('Interrupted preparation')
        yield (1,)*len(q.ciphertext.words)
    monkeypatch.setattr(b.midpoint_grouped,'proposals',proposals)
    with pytest.raises(RuntimeError,match='Interrupted'):b.prepare()
    partial=json.loads((tmp_path/'prepared.json').read_text())
    assert not partial['complete'] and len(partial['cases'])==1
    source,p=b.prepare()
    assert p['complete'] and len(p['cases'])==2 and len(calls)==3
