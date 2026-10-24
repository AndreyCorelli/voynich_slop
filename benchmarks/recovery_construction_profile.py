"""Profile model construction up to the first solver check on preserved inputs."""
import argparse
import cProfile
from dataclasses import asdict
import json
import hashlib
from pathlib import Path
import platform
import pstats
from time import perf_counter
from unittest.mock import patch

import z3
from benchmarks import training_diversity_indexed as indexed
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest

OUT=Path('experiments/results/recovery-construction-profile')


def profile_construction(q,solver=indexed.solve):
    profiler=cProfile.Profile();original=z3.Solver.check;checks=[]
    def check(self,*args,**kwargs):
        profiler.disable()
        checks.append(True)
        return original(self,*args,**kwargs)
    start=perf_counter()
    with patch.object(z3.Solver,'check',check):
        profiler.enable()
        try:result=solver(q)
        finally:profiler.disable()
    if len(checks)!=1:raise RuntimeError('Expected exactly one unprofiled solver check')
    return result,profiler,perf_counter()-start


def summarize(profiler):
    stats=pstats.Stats(profiler)
    rows=[{'file':f,'line':line,'function':name,'primitive_calls':cc,'calls':nc,
           'self_seconds':tt,'cumulative_seconds':ct} for (f,line,name),(cc,nc,tt,ct,callers) in stats.stats.items()]
    membership=[r for r in rows if r['file'].endswith('/solver/dictionary_encoding.py') and r['function']=='membership']
    return {'profile_seconds':stats.total_tt,'total_calls':stats.total_calls,
        'dictionary_membership':membership,
        'top_cumulative':sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:30],
        'top_self':sorted(rows,key=lambda r:r['self_seconds'],reverse=True)[:30],
        'interpretation':'Cumulative entries overlap; do not sum them. Self times partition profiled work. Profiling stops immediately before first Z3 check; all reported construction timings include profiler overhead.'}


def prepare():
    source,baseline,public=indexed.prepare()
    previous=json.loads((indexed.OUT/'report.json').read_text())
    if not previous['complete'] or previous['prepared_sha256']!=digest(public):raise ValueError('Unmatched unprofiled baseline')
    identity={'public_sha256':digest(public),'source_sha256':digest(source),'baseline_sha256':digest(previous),
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path('benchmarks/training_diversity_indexed.py'),
             Path('src/voynich_smt/language/dictionary.py'),Path('src/voynich_smt/solver/recovery.py'),
             Path('src/voynich_smt/solver/observed_codes.py'),Path('src/voynich_smt/solver/dictionary_encoding.py'),
             Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen code or sources changed')
        return source,p
    cases=[dict(c,unprofiled_baseline=next(r for r in previous['cases'] if r['id']==c['id'])) for c in public['cases']]
    protocol={'identity':identity,'case_ids':indexed.CASE_IDS,'timeout_ms_per_fit':5000,'profiles_per_case':1,
        'environment':{'python':platform.python_version(),'z3':z3.get_version_string(),'platform':platform.platform()},
        'scope':'Same public hidden requests; no oracle lengths or language scoring. cProfile enabled only during construction, disabled before first ordinary Z3 check via temporary instrumentation. No production constraint/model changes. Solver still runs with existing timeout, results verified and frozen-scored if SAT. Profiling overhead invalidates direct construction timing comparisons; cumulative entries overlap. Sequential isolated runs; completed cases checkpoint.'}
    p={'identity':identity,'protocol':protocol,'cases':cases}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return source,p


def run():
    source,p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(row['id']==case['id'] for row in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        original=next(c for c in source['cases'] if c['id']==case['id']);verify(q,original['truth'])
        print(case['id'],'profiling construction only; solver timeout=5000ms',flush=True)
        recovered,profiler,wall=profile_construction(q);result=asdict(recovered);verify(q,result)
        if result['status']=='UNSAT':raise RuntimeError('Known positive returned UNSAT')
        profile_path=OUT/(case['id']+'.prof');profiler.dump_stats(str(profile_path))
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall,
            'profile_path':str(profile_path),'profile_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            'summary':summarize(profiler)}
        row.update(evaluate(original,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"profiled construction={result['capacity']['construction_seconds']:.2f}s",f"solver={result['runtime_seconds']:.2f}s",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    import hashlib
    source,p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and tuple(c['id'] for c in r['cases'])==indexed.CASE_IDS
    for row,case in zip(r['cases'],p['cases']):
        q=HiddenRecoveryRequest.from_dict(case['request']);assert row['request_sha256']==digest(asdict(q))
        original=next(c for c in source['cases'] if c['id']==case['id']);verify(q,row['result'])
        assert not row['result']['capacity'].get('oracle_word_lengths',False)
        path=Path(row['profile_path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['profile_sha256']
        assert digest(summarize(str(path)))==digest(row['summary'])
        assert all(digest(row[k])==digest(v) for k,v in evaluate(original,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'checks':['code/source hashes','matched requests','profile file hashes and summaries','no oracle lengths','result verification and frozen scoring']})
    print('Validated two construction profiles without repeating fits')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared two construction-only profiles; use --run')
