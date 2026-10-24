import json
from itertools import islice
from benchmarks import full_vocabulary_h1_public_lengths as b
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.recovery import Recovery
from voynich_smt.solver.length_search import ranked_vectors


def request():
    p=json.loads((b.SOURCE/'prepared.json').read_text())
    return HiddenRecoveryRequest.from_dict(p['requests']['full'])


def test_ranked_enumeration_complete_unique():
    vectors=list(ranked_vectors(((3,1,2),(2,1))))
    assert len(vectors)==len(set(vectors))==6
    assert vectors[0]==(3,2)


def test_proposals_use_only_public_request_and_respect_repeats():
    q=request()
    vectors=list(islice(b.proposals(q),3))
    assert vectors==list(islice(b.proposals(q),3))
    assert all(v[i]==v[j] for v in vectors for i,w in enumerate(q.ciphertext.words)
               for j,x in enumerate(q.ciphertext.words) if w==x)
    assert all(len(v)==len(q.ciphertext.words) for v in vectors)


def test_shared_budget_and_no_global_unsat():
    q=request();budgets=[]
    def solver(vector,request):
        budgets.append(request.timeout_ms)
        return Recovery('UNSAT',2.0)
    r=b.search(q,[(1,)*18]*3,solver)
    assert budgets==[5000,3000,1000]
    assert r['status']=='UNKNOWN'
    assert all('oracle_word_lengths' not in a['result']['capacity'] for a in r['attempts'])


def test_unknown_consuming_budget_stops():
    def solver(vector,q):return Recovery('UNKNOWN',5.01)
    r=b.search(request(),[(1,)*18]*3,solver)
    assert len(r['attempts'])==1 and r['status']=='UNKNOWN'
