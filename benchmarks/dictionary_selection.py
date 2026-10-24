"""Compare entry selectors with saved equivalent trie synthetic controls."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
from time import perf_counter
import z3
from benchmarks.cycle_performance import solve
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def run(config, output, artifacts):
    if (set(config) != {'source_report','seed','timeout_ms','full_retry_timeout_ms'}
            or type(config['seed']) is not int or any(type(config[k]) is not int or config[k] <= 0
                for k in ('timeout_ms','full_retry_timeout_ms'))):
        raise ValueError('Invalid dictionary selection configuration')
    source=json.loads(Path(config['source_report']).read_text())
    if not source['complete']:raise ValueError('Completed baseline report required')
    rows=sorted((r for r in source['experiments'] if r['seed']==config['seed']
                 and r['cycle_encoding']=='state'),key=lambda r:r['vocabulary_size'])
    if not rows:raise ValueError('No matching baseline controls')
    report={'config':config,'source_sha256':digest(source),'experiments':[], 'complete':False,
        'environment':{'python':platform.python_version(),'z3':z3.get_version_string()},
        'semantics':'Same public synthetic requests; only dictionary membership formula and explicit retry budget differ'}
    write_json(output,report)
    for baseline in rows:
        payload=json.loads(Path(baseline['public_input']).read_text())
        if digest(payload)!=baseline['input_sha256']:raise ValueError('Baseline input hash mismatch')
        original=HiddenRecoveryRequest.from_dict(payload['request'])
        verify(original,baseline['result'])
        for timeout in ([config['timeout_ms'],config['full_retry_timeout_ms']]
                if baseline==rows[-1] and config['full_retry_timeout_ms']!=config['timeout_ms']
                else [config['timeout_ms']]):
            request=replace(original,dictionary_encoding='entry',timeout_ms=timeout)
            wrapper={'request':asdict(request),'cycle_encoding':'state'}
            name=f'seed-{config["seed"]}-vocab-{baseline["vocabulary_size"]}-entry-ms{timeout}'
            path=artifacts/'inputs'/f'{name}.json';write_json(path,wrapper)
            print(name,flush=True)
            begin=perf_counter();result=asdict(solve(request,'state'));verify(request,result)
            if result['status']=='UNSAT':raise RuntimeError('Known positive control incorrectly UNSAT')
            row={'id':name,'public_input':str(path),'input_sha256':digest(wrapper),'truth':baseline['truth'],
                'baseline_id':baseline['id'],'baseline_timeout_ms':original.timeout_ms,
                'baseline_result':baseline['result'],'baseline_wall_seconds':baseline['wall_seconds'],
                'wall_seconds':perf_counter()-begin,'result':result}
            report['experiments'].append(row);write_json(output,report)
            print(f'{result["status"]}: solver={result["runtime_seconds"]:.3f}s wall={row["wall_seconds"]:.3f}s',flush=True)
            if result['status']=='SAT':break
    report.update(complete=True,full_vocabulary_recovered=any(r['result']['status']=='SAT'
        and r['baseline_id']==rows[-1]['id'] for r in report['experiments']))
    long=Path('experiments/results/seed-7-state-30min.json')
    if long.exists() and config['seed']==7:
        long_report=json.loads(long.read_text())
        long_request=HiddenRecoveryRequest.from_dict(long_report['request'])
        largest=json.loads(Path(rows[-1]['public_input']).read_text())
        reference=HiddenRecoveryRequest.from_dict(largest['request'])
        if replace(long_request,timeout_ms=reference.timeout_ms)==reference:
            verify(long_request,long_report['result'])
            report['long_trie_baseline']={'path':str(long),'sha256':digest(long_report),
                'timeout_ms':long_request.timeout_ms,'status':long_report['result']['status'],
                'runtime_seconds':long_report['result']['runtime_seconds']}
    write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='experiments/configs/dictionary-selection.json')
    parser.add_argument('--output',default='experiments/results/dictionary-selection.json')
    parser.add_argument('--artifacts',default='data/generated/dictionary-selection')
    args=parser.parse_args()
    run(json.loads(Path(args.config).read_text()),Path(args.output),Path(args.artifacts))


if __name__=='__main__':main()
