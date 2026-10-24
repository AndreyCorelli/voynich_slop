"""Fresh hidden recovery timings after flat dictionary equality reuse."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter

from benchmarks import training_diversity as diversity
import platform
import z3
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/equality-reuse')
CASE_IDS=('fixed-two-seed-3101-types-36','mixed-one-two-three-seed-3101-types-36')


def solve(q):
    # No lengths, training plaintext, key, segmentation or continuation supplied.
    return recover_observed_codes(q)


def prepare():
    source=diversity.prepare()
    old=json.loads(Path('experiments/results/training-diversity-indexed/report.json').read_text())
    if not old['complete']:raise ValueError('Hidden baseline incomplete')
    profile_protocol=json.loads(Path('experiments/results/recovery-construction-profile/protocol.json').read_text())
    if digest(Path('experiments/results/equality-reuse/reference_dictionary_encoding.py').read_text())!=profile_protocol['identity']['code_sha256']['src/voynich_smt/solver/dictionary_encoding.py']:raise ValueError('Original encoding snapshot does not match profiled implementation')
    baseline=json.loads((diversity.OUT/'report.json').read_text())
    if not baseline['complete'] or baseline['prepared_sha256']!=digest(source):raise ValueError('Unmatched length-only baseline')
    identity={'source_sha256':digest(source),'baseline_sha256':digest(baseline),'previous_hidden_report_sha256':digest(old),'reference_profile_protocol_sha256':digest(profile_protocol),
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path('src/voynich_smt/solver/dictionary_encoding.py'),Path('experiments/results/equality-reuse/reference_dictionary_encoding.py'),Path('src/voynich_smt/language/dictionary.py'),Path('src/voynich_smt/solver/observed_codes.py'),
             Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/public_length_calibration.py'),
             Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        prepared=json.loads(path.read_text())
        if prepared['identity']!=identity:raise ValueError('Frozen inputs or implementation changed')
        return source,baseline,prepared
    cases=[]
    for case_id in CASE_IDS:
        case=next(c for c in source['cases'] if c['id']==case_id)
        previous=next(c for c in baseline['cases'] if c['id']==case_id)
        q=HiddenRecoveryRequest.from_dict(case['request']);verify(q,case['truth']);verify(q,previous['result'])
        if previous['result']['status']!='SAT' or previous['exact_words']!=3:raise ValueError('Expected successful length-only control')
        if previous['request_sha256']!=digest(asdict(q)):raise ValueError('Baseline request changed')
        previous_hidden=next(c for c in old['cases'] if c['id']==case_id)
        if previous_hidden['request_sha256']!=digest(asdict(q)):raise ValueError('Unmatched previous hidden request')
        cases.append({'previous_hidden':{'status':previous_hidden['result']['status'],'construction_seconds':previous_hidden['construction_seconds'],'solver_seconds':previous_hidden['result']['runtime_seconds'],'fit_wall_seconds':previous_hidden['fit_wall_seconds']},'id':case_id,'request':asdict(q),'request_sha256':digest(asdict(q)),
            'baseline_exact_words':previous['exact_words'],'baseline_solver_seconds':previous['result']['runtime_seconds']})
    protocol={'identity':identity,'case_ids':CASE_IDS,'fits_per_case':1,'timeout_ms_per_fit':5000,
        'environment':{'python':platform.python_version(),'platform':platform.platform(),'z3':z3.get_version_string()},
        'semantics':'Fresh timing after exact-AST-equivalent local equality reuse in flat dictionary membership; historical reports preserved. Original 72-word training ciphertext and full dictionary, alphabets, H1 L1-3, free selection and observed domains. Plaintext identities, lengths, key and segmentation all hidden; no public length branches or language scoring. Same solver budget as length-only controls. No held-out information passed to solver. Two outcome-selected synthetic positives; UNKNOWN unresolved. Construction outside solver budget; report separately. Checkpoint completed fits, no retries or tuning.'}
    prepared={'identity':identity,'protocol':protocol,'cases':cases}
    write_json(OUT/'protocol.json',protocol);write_json(path,prepared)
    return source,baseline,prepared


def run():
    source,baseline,p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for prepared in p['cases']:
        if any(c['id']==prepared['id'] for c in r['cases']):continue
        case=next(c for c in source['cases'] if c['id']==prepared['id'])
        q=HiddenRecoveryRequest.from_dict(prepared['request'])
        print(prepared['id'],'hidden words and lengths; solver budget=5000ms (construction extra)',flush=True)
        start=perf_counter();result=asdict(solve(q));wall=perf_counter()-start
        verify(q,result)
        if result['status']=='UNSAT':raise RuntimeError('Independently verified positive returned UNSAT')
        row={'id':prepared['id'],'request_sha256':prepared['request_sha256'],'result':result,
            'fit_wall_seconds':wall,'construction_seconds':result.get('capacity',{}).get('construction_seconds'),
            'baseline_exact_words':prepared['baseline_exact_words'],'baseline_solver_seconds':prepared['baseline_solver_seconds'],'previous_hidden':prepared['previous_hidden']}
        if result['status']=='SAT':
            row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],case['truth']['plaintext']['words']))
        row.update(evaluate(case,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.2f}s",f"construction={row['construction_seconds']}",f"exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    source,baseline,p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p)
    assert tuple(c['id'] for c in r['cases'])==CASE_IDS
    for row,prepared in zip(r['cases'],p['cases']):
        case=next(c for c in source['cases'] if c['id']==row['id'])
        q=HiddenRecoveryRequest.from_dict(prepared['request'])
        assert row['request_sha256']==digest(asdict(q))==digest(case['request'])
        verify(q,case['truth']);verify(q,row['result'])
        assert not row['result'].get('capacity',{}).get('oracle_word_lengths',False)
        assert row['baseline_exact_words']==prepared['baseline_exact_words']==3
        assert row['baseline_solver_seconds']==prepared['baseline_solver_seconds']
        assert row['previous_hidden']==prepared['previous_hidden']
        assert row['construction_seconds']==row['result'].get('capacity',{}).get('construction_seconds')
        if row['result']['status']=='SAT':
            assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],case['truth']['plaintext']['words']))
        assert all(digest(row[k])==digest(v) for k,v in evaluate(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'cases':2,'checks':['hashes','matched requests and baselines','synthetic and recovered witnesses','no oracle length metadata','independent frozen scoring']})
    print('Validated two equality-reuse hidden-recovery records')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared two equality-reuse hidden-recovery fits. Use --run.')
