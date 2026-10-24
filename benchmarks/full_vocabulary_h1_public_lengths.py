"""Fixed-budget public midpoint length search; no truth in proposal generation."""
from dataclasses import asdict, replace
from itertools import islice
import json
from math import ceil
from pathlib import Path

from benchmarks.full_vocabulary_h1_lengths import SOURCE, solve
from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.length_search import public_domains, ranked_vectors

OUT=Path('experiments/results/full-vocabulary-h1-public-lengths')


def proposals(q):
    domains, graph=public_domains(q)
    span=q.bounds.min_code_length+q.bounds.max_code_length
    ranked=tuple(tuple(sorted(d,key=lambda n:(abs(n*span-2*len(w)),n)))
                 for d,w in zip(domains,q.ciphertext.words))
    for vector in ranked_vectors(ranked):
        if any((r.prefix=='equal' and vector[r.left]!=vector[r.right])
               or (r.prefix=='left' and vector[r.left]>=vector[r.right])
               or (r.prefix=='right' and vector[r.left]<=vector[r.right])
               for r in graph.relations):continue
        yield vector


def search(q, vectors, solver=solve):
    attempts=[];remaining=q.timeout_ms
    for vector in vectors:
        if remaining<=0:break
        result=asdict(solver(vector,replace(q,timeout_ms=remaining)))
        result['capacity'].pop('oracle_word_lengths',None)
        result['capacity'].update(word_length_source='public_midpoint_search',fixed_word_lengths=list(vector))
        verify(q,result)
        attempts.append({'word_lengths':vector,'budget_ms':remaining,'result':result})
        remaining-=ceil(result['runtime_seconds']*1000)
        if result['status']=='SAT':break
    return {'status':'SAT' if attempts and attempts[-1]['result']['status']=='SAT' else 'UNKNOWN',
            'attempts':attempts,'remaining_solver_budget_ms':max(0,remaining),
            'solver_seconds':sum(a['result']['runtime_seconds'] for a in attempts)}


def run():
    if (OUT/'protocol.json').exists():raise ValueError('Fixed experiment already started; preserve it')
    p=json.loads((SOURCE/'prepared.json').read_text())
    q=HiddenRecoveryRequest.from_dict(p['requests']['full'])
    # Freeze public schedule before reading any generating plaintext or continuation.
    vectors=tuple(islice(proposals(q),3))
    protocol={'request_sha256':digest(asdict(q)),'source_sha256':digest(p),
        'timeout_ms':q.timeout_ms,'max_branches':3,'scheduled_vectors':vectors,
        'ordering':'Distance from ciphertext length divided by code-bound midpoint; ties shorter first. Sum of per-word preference ranks; public prefix relations enforced.',
        'limitations':'Retrospective heuristic on a previously diagnosed fixed-length-two fixture. No truth supplied to proposals; this is not blind calibration or evidence of fixed-length Voynich codes. Non-SAT branches never establish global UNSAT.',
        'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path('src/voynich_smt/solver/length_search.py'),Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/full_vocabulary_h1_lengths.py'))}}
    write_json(OUT/'protocol.json',protocol)
    report=search(q,vectors);report.update(protocol=protocol,complete=True,evaluation_status='NOT_EVALUATED_NO_SAT')
    if report['status']=='SAT':
        result=report['attempts'][-1]['result']
        enc=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
        held=Text(tuple(tuple(w) for w in p['holdout']['words']))
        prediction=score(held,enc,q.dictionary,q.ciphertext.words)
        exact=sum(w['fully_decoded'] and tuple(w['decoded_prefix'])==tuple(t) for w,t in zip(prediction['word_results'],p['holdout_plaintext']['words']))
        report.update(prediction=prediction,exact_words=exact,evaluation_status='EVALUATED_FROZEN_KEY')
    write_json(OUT/'report.json',report)
    print(report['status'],f"solver={report['solver_seconds']:.2f}s",f"exact={report.get('exact_words')}")
    return report

if __name__=='__main__':run()
