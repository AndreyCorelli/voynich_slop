"""Calibrate truth-free public length orderings on saved synthetic controls."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
from time import perf_counter
import z3
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.length_search import search


def run(config, output, artifacts):
    required = {'public_inputs','branch_timeout_ms','max_branches'}
    orderings = config.get('orderings',['shortest_first'])
    if (not required <= set(config) or set(config)-required-{'orderings'} or not config['public_inputs']
            or not isinstance(orderings,list) or not orderings
            or any(o not in {'shortest_first','balanced','candidate_rich'} for o in orderings)
            or len(set(orderings)) != len(orderings)
            or any(type(config[k]) is not int or config[k] <= 0 for k in ('branch_timeout_ms','max_branches'))):
        raise ValueError('Invalid public length search configuration')
    report = {'config':config,'environment':{'python':platform.python_version(),'z3':z3.get_version_string()},
        'semantics':'Only public ciphertext and vocabulary drive length branches; no truth loaded',
        'cases':[], 'complete':False}
    write_json(output,report)
    cases = [(name, ordering) for name in config['public_inputs'] for ordering in orderings]
    for ci, (name, ordering) in enumerate(cases):
        payload = json.loads(Path(name).read_text())
        if set(payload) != {'request','cycle_encoding'} or payload['cycle_encoding'] != 'state':
            raise ValueError('Expected an ordinary state-cycle public input without oracle data')
        request = replace(HiddenRecoveryRequest.from_dict(payload['request']),timeout_ms=config['branch_timeout_ms'])
        case={'source_input':name,'source_sha256':digest(payload),'word_count':len(request.ciphertext.words),
              'ordering':ordering,'attempts':[],'complete':False}
        report['cases'].append(case)
        def record(index, vector, result):
            verify(request,asdict(result))
            wrapper={'request':asdict(request),'word_lengths':list(vector)}
            path=artifacts/'inputs'/f'case-{ci:02d}-branch-{index:03d}.json';write_json(path,wrapper)
            case['attempts'].append({'word_lengths':list(vector),'public_input':str(path),
                'input_sha256':digest(wrapper),'result':asdict(result)})
            write_json(output,report)
            print(f'  {index}: {list(vector)} => {result.status} ({result.runtime_seconds:.3f}s)',flush=True)
        print(f'Case {ci}: {case["word_count"]} words; {ordering}',flush=True)
        begin=perf_counter(); summary=search(request,config['max_branches'],record,ordering=ordering)
        case.update({k:v for k,v in summary.items() if k!='attempts'},wall_seconds=perf_counter()-begin,complete=True)
        write_json(output,report)
    report['complete']=True;write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='experiments/configs/length-search.json')
    parser.add_argument('--output',default='experiments/results/length-search.json')
    parser.add_argument('--artifacts',default='data/generated/length-search')
    args=parser.parse_args()
    run(json.loads(Path(args.config).read_text()),Path(args.output),Path(args.artifacts))


if __name__=='__main__':main()
