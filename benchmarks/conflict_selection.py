"""Compare selection rules on the certified 22-word restored-vocabulary conflict."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks.clean_latin_suffix import validate_row
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.solver.observed_codes import recover_observed_codes


def selection_variants(base,timeout_ms):
    if base.selection!=HomophoneSelection('cycle','text'):
        raise ValueError('Expected text-wide cyclic baseline')
    return {'free':replace(base,selection=HomophoneSelection(),timeout_ms=timeout_ms),
            'word-reset':replace(base,selection=HomophoneSelection('cycle','word'),timeout_ms=timeout_ms)}


def run(timeout_ms=30000,resume=False,prepare_only=False):
    source_path=Path('experiments/results/clean-latin-suffix.json')
    source=json.loads(source_path.read_text())
    if not source['complete'] or not source['boundary']['minimality_proven']:
        raise ValueError('Certified suffix boundary required')
    original=json.loads(Path(source['source_report']).read_text())
    if digest(original)!=source['source_sha256']:raise ValueError('Baseline source hash mismatch')
    full=HiddenRecoveryRequest.from_dict(original['request'])
    count=source['boundary']['smallest_proved_unsat']
    row=next(r for r in source['experiments'] if r['word_count']==count and r['result']['status']=='UNSAT')
    base=validate_row(row,full)
    if count!=22 or source['conflict']['start']!=1 or source['conflict']['end']!=23:
        raise ValueError('Expected the fixed words 2–23 conflict')
    variants=selection_variants(base,timeout_ms)
    prepared=[]
    for name,request in variants.items():
        payload={'request':asdict(request),'codeword_domains':'observed'}
        path=Path('data/generated/conflict-selection/inputs')/(name+'.json')
        prepared.append({'id':name,'public_input':str(path),'input_sha256':digest(payload),
                         'request':asdict(request)})
    config={'timeout_ms':timeout_ms,'source_sha256':digest(source),'baseline_input_sha256':row['input_sha256']}
    output=Path('experiments/results/conflict-selection.json')
    report={'schema_version':1,'config':config,'config_sha256':digest(config),
            'source_report':str(source_path),'baseline_result':row['result'],
            'baseline_request':asdict(base),'baseline_input_sha256':row['input_sha256'],
            'semantics':'Only selection policy and timeout change. Free choice relaxes text-wide cycles; word-reset cycles are a different policy, not a superset. Same fixed 22-word block, 5658-entry vocabulary, H2/L3 bounds and observed domains; no hidden hints.',
            'prepared_inputs':prepared,'experiments':[],'complete':False}
    if resume and output.exists():
        previous=json.loads(output.read_text())
        if previous['config_sha256']!=digest(config):
            raise ValueError('Resume requires identical source and solver budget')
        report=previous
        for cached in report['experiments']:
            q=HiddenRecoveryRequest.from_dict(cached['request'])
            if q!=variants[cached['id']] or cached['input_sha256']!=digest({'request':asdict(q),'codeword_domains':'observed'}):
                raise ValueError('Cached variant request mismatch')
            verify(q,cached['result'])
    # Validate a resumed report before replacing any prepared input.
    for entry in prepared:
        write_json(entry['public_input'],{'request':entry['request'],'codeword_domains':'observed'})
    write_json(output,report)
    if prepare_only:return report
    done={e['id'] for e in report['experiments']}
    for entry in prepared:
        name=entry['id']
        if name in done:continue
        request=variants[name]
        print(f'{name}: 22-word conflict; budget={timeout_ms}ms',flush=True)
        begin=perf_counter();result=asdict(recover_observed_codes(request));verify(request,result)
        report['experiments'].append({**entry,'result':result,'wall_seconds':perf_counter()-begin})
        write_json(output,report)
        print(f"  {result['status']}; verified={result['verified']}; solver={result['runtime_seconds']:.2f}s",flush=True)
    report['complete']=True;write_json(output,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms',type=int,default=30000)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args();run(args.timeout_ms,args.resume,args.prepare_only)
