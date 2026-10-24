"""Frozen public midpoint search on two preserved 36-type positives."""
import argparse
from dataclasses import asdict
from itertools import islice
import json
from math import ceil
from pathlib import Path
from time import perf_counter

from benchmarks import training_diversity_hidden as hidden
from benchmarks import full_vocabulary_h1_public_lengths as midpoint
from benchmarks import midpoint_grouped
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest

OUT=Path('experiments/results/training-diversity-midpoint')


def prepare():
    source,baseline,public=hidden.prepare()
    hidden_report=json.loads((hidden.OUT/'report.json').read_text())
    if not hidden_report['complete'] or hidden_report['prepared_sha256']!=digest(public):raise ValueError('Unmatched hidden baseline')
    identity={'source_sha256':digest(source),'public_sha256':digest(public),'hidden_report_sha256':digest(hidden_report),
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path(midpoint.__file__),Path(midpoint_grouped.__file__),Path('src/voynich_smt/solver/length_search.py'),
             Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/full_vocabulary_h1_lengths.py'),
             Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen sources or code changed')
        if p.get('complete',False):return source,p
        cases=p['cases']
    else:cases=[]
    write_json(path,{'identity':identity,'cases':cases,'complete':False})
    for case in public['cases']:
        if any(c['id']==case['id'] for c in cases):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        start=perf_counter();vectors=tuple(islice(midpoint_grouped.proposals(q),3))
        cases.append(dict(case,scheduled_vectors=vectors,schedule_seconds=perf_counter()-start))
        write_json(path,{'identity':identity,'cases':cases,'complete':False})
    protocol={'identity':identity,'case_ids':hidden.CASE_IDS,'timeout_ms_per_case':5000,'max_branches':3,
        'semantics':'Unchanged frozen midpoint rule on public requests only; no truth-derived lengths, plaintext, key, continuation or profile in proposal function. Shared solver budget across up to three branches; construction and schedule generation outside budget. SAT full verified witness; non-SAT search always UNKNOWN, never global UNSAT. Completed cases checkpoint. Two selected synthetic positives, no blind/general manuscript claim.'}
    p={'identity':identity,'protocol':protocol,'cases':cases,'complete':True}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return source,p


def run():
    source,p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(c['id']==case['id'] for c in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        print(case['id'],'public midpoint; shared solver budget=5000ms (construction extra)',flush=True)
        start=perf_counter();search=midpoint.search(q,case['scheduled_vectors']);wall=perf_counter()-start
        result=search['attempts'][-1]['result'] if search['status']=='SAT' else {'status':'UNKNOWN'}
        original=next(c for c in source['cases'] if c['id']==case['id'])
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'search':search,'result':result,
            'fit_wall_seconds':wall,'schedule_seconds':case['schedule_seconds'],
            'construction_seconds':sum(a['result']['capacity'].get('construction_seconds',0) for a in search['attempts'])}
        if result['status']=='SAT':
            row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],original['truth']['plaintext']['words']))
        row.update(evaluate(original,q,result));r['cases'].append(row);write_json(path,r)
        print(search['status'],f"solver={search['solver_seconds']:.2f}s",f"construction={row['construction_seconds']:.2f}s",f"exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    source,p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p)
    assert tuple(c['id'] for c in r['cases'])==hidden.CASE_IDS
    for case,row in zip(p['cases'],r['cases']):
        q=HiddenRecoveryRequest.from_dict(case['request'])
        assert row['request_sha256']==digest(asdict(q))
        assert digest(case['scheduled_vectors'])==digest(tuple(islice(midpoint_grouped.proposals(q),3)))
        original=next(c for c in source['cases'] if c['id']==case['id']);verify(q,original['truth'])
        remaining=5000
        for index,a in enumerate(row['search']['attempts']):
            assert remaining>0 and a['budget_ms']==remaining
            assert digest(a['word_lengths'])==digest(case['scheduled_vectors'][index])
            remaining-=ceil(a['result']['runtime_seconds']*1000)
            verify(q,a['result'])
            assert a['result']['capacity']['word_length_source']=='public_midpoint_search'
            assert not a['result']['capacity'].get('oracle_word_lengths',False)
            if a['result']['status']=='SAT':assert list(map(len,a['result']['plaintext']['words']))==a['word_lengths']
        assert row['search']['remaining_solver_budget_ms']==max(0,remaining)
        assert row['search']['solver_seconds']==sum(a['result']['runtime_seconds'] for a in row['search']['attempts'])
        assert row['result']['status']==row['search']['status']
        if row['result']['status']=='SAT':
            assert row['result']==row['search']['attempts'][-1]['result']
            assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],original['truth']['plaintext']['words']))
        assert all(digest(row[k])==digest(v) for k,v in evaluate(original,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'cases':2,'checks':['hashes','public schedules','budget consumption','full witnesses and branch lengths','oracle metadata absent','frozen scoring']})
    print('Validated two public-midpoint records')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared two public-midpoint searches; use --run (construction extra).')
