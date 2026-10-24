"""Compare observed substring domains with exact saved hidden-control baselines."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
import z3
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.observed_codes import recover_observed_codes


def replay(payload):
    if set(payload) != {'request','codeword_domains'} or payload['codeword_domains'] != 'observed':
        raise ValueError('Expected an observed-domain public replay wrapper')
    request=HiddenRecoveryRequest.from_dict(payload['request'])
    result=recover_observed_codes(request)
    verify(request,asdict(result))
    return result


def run(config,output,artifacts):
    if (set(config) != {'source_report','word_counts','timeout_ms'} or not config['word_counts']
            or any(type(n) is not int or n<=0 for n in config['word_counts'])
            or type(config['timeout_ms']) is not int or config['timeout_ms']<=0):
        raise ValueError('Invalid observed-domain configuration')
    source=json.loads(Path(config['source_report']).read_text())
    if not source['complete']:raise ValueError('Completed baseline report required')
    report={'config':config,'source_sha256':digest(source),'experiments':[],'complete':False,
        'environment':{'python':platform.python_version(),'z3':z3.get_version_string()},
        'semantics':'Same full-vocabulary public controls; no truth loaded; explicit redundant used-codeword domains'}
    write_json(output,report)
    for count in config['word_counts']:
        baseline=next(r for r in source['experiments'] if r['word_count']==count)
        public=json.loads(Path(baseline['public_input']).read_text())
        if digest(public)!=baseline['input_sha256']:raise ValueError('Baseline input hash mismatch')
        original=HiddenRecoveryRequest.from_dict(public['request'])
        if original.timeout_ms!=config['timeout_ms'] or public['cycle_encoding']!='state':
            raise ValueError('Matched baseline timeout and state-cycle formula required')
        verify(original,baseline['result'])
        payload={'request':asdict(original),'codeword_domains':'observed'}
        path=artifacts/'inputs'/f'words-{count:02d}.json';write_json(path,payload)
        print(f'{count} words: explicit substring domains, {original.timeout_ms}ms',flush=True)
        begin=perf_counter();result=asdict(replay(payload))
        row={'word_count':count,'public_input':str(path),'input_sha256':digest(payload),
            'baseline_input':baseline['public_input'],'baseline_input_sha256':digest(public),
            'baseline_result':baseline['result'],'baseline_wall_seconds':baseline['wall_seconds'],
            'wall_seconds':perf_counter()-begin,'result':result}
        report['experiments'].append(row);write_json(output,report)
        print(f'  {result["status"]}: solver={result["runtime_seconds"]:.3f}s wall={row["wall_seconds"]:.3f}s',flush=True)
        if result['status']=='UNSAT':raise RuntimeError('Known positive control incorrectly UNSAT')
    report['complete']=True;write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='experiments/configs/observed-codes.json')
    parser.add_argument('--output',default='experiments/results/observed-codes.json')
    parser.add_argument('--artifacts',default='data/generated/observed-codes')
    parser.add_argument('--replay')
    parser.add_argument('--timeout-ms',type=int,help='Override only the replay solver budget')
    parser.add_argument('--replay-output',help='Save effective request, result and timing as JSON')
    args=parser.parse_args()
    if (args.timeout_ms is not None or args.replay_output) and not args.replay:
        parser.error('--timeout-ms and --replay-output require --replay')
    if args.timeout_ms is not None and args.timeout_ms<=0:
        parser.error('--timeout-ms must be positive')
    if args.replay:
        payload=json.loads(Path(args.replay).read_text())
        if args.timeout_ms is not None:
            request=replace(HiddenRecoveryRequest.from_dict(payload['request']),timeout_ms=args.timeout_ms)
            payload={**payload,'request':asdict(request)}
        print(f'Replaying {args.replay}; solver budget {payload["request"]["timeout_ms"]}ms',file=sys.stderr,flush=True)
        begin=perf_counter();result=asdict(replay(payload))
        if args.replay_output:
            report={**payload,'source_input':args.replay,'input_sha256':digest(payload),
                'wall_seconds':perf_counter()-begin,'result':result,'complete':True,
                'environment':{'python':platform.python_version(),'z3':z3.get_version_string()}}
            write_json(Path(args.replay_output),report)
            print(f'{result["status"]}; verified={result["verified"]}; '
                  f'solver={result["runtime_seconds"]:.2f}s; saved {args.replay_output}',flush=True)
        else:print(json.dumps(result))
    else:run(json.loads(Path(args.config).read_text()),Path(args.output),Path(args.artifacts))


if __name__=='__main__':main()
