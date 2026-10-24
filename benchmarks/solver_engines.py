"""Compare solver engines on exactly the same public fixed-length branch."""
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
from voynich_smt.solver.segmented import recover_with_word_lengths


def replay(payload):
    if set(payload) != {'request','word_lengths','solver_backend'}:
        raise ValueError('Expected an explicit solver-engine branch wrapper')
    request=HiddenRecoveryRequest.from_dict(payload['request'])
    result=recover_with_word_lengths(request,payload['word_lengths'],solver_backend=payload['solver_backend'])
    result.capacity.pop('oracle_word_lengths',None)
    result.capacity.update(word_length_source='public_search',fixed_word_lengths=payload['word_lengths'])
    verify(request,asdict(result))
    return result


def run(config,output,artifacts):
    if (set(config) != {'public_input','timeout_ms'} or type(config['timeout_ms']) is not int or config['timeout_ms']<=0):
        raise ValueError('Invalid engine comparison configuration')
    original=json.loads(Path(config['public_input']).read_text())
    if set(original) != {'request','word_lengths'}:
        raise ValueError('Expected public length-search branch input')
    request=replace(HiddenRecoveryRequest.from_dict(original['request']),timeout_ms=config['timeout_ms'])
    report={'config':config,'source_sha256':digest(original),'experiments':[],'complete':False,
        'environment':{'python':platform.python_version(),'z3':z3.get_version_string()},
        'scope':'Identical finite representation and public word lengths; only solver backend changes'}
    write_json(output,report)
    for backend in ('qffd','smt'):
        payload={'request':asdict(request),'word_lengths':original['word_lengths'],'solver_backend':backend}
        path=artifacts/'inputs'/f'{backend}.json';write_json(path,payload)
        print(f'{backend}: {len(request.ciphertext.words)} words, {request.timeout_ms}ms, lengths {original["word_lengths"]}',flush=True)
        begin=perf_counter();result=asdict(replay(payload))
        row={'solver_backend':backend,'public_input':str(path),'input_sha256':digest(payload),
             'wall_seconds':perf_counter()-begin,'result':result}
        report['experiments'].append(row);write_json(output,report)
        print(f'  {result["status"]}: solve={result["runtime_seconds"]:.3f}s wall={row["wall_seconds"]:.3f}s',flush=True)
    fingerprints={r['result']['capacity']['formula_sha256'] for r in report['experiments']}
    if len(fingerprints)!=1:raise RuntimeError('Engine comparison formulas differ')
    report['identical_formula_sha256']=next(iter(fingerprints))
    statuses={r['result']['status'] for r in report['experiments']}
    if statuses=={'SAT','UNSAT'}:raise RuntimeError('Equivalent engine formulations disagree on feasibility')
    report['complete']=True;write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='experiments/configs/solver-engines.json')
    parser.add_argument('--output',default='experiments/results/solver-engines.json')
    parser.add_argument('--artifacts',default='data/generated/solver-engines')
    parser.add_argument('--replay')
    args=parser.parse_args()
    if args.replay:print(json.dumps(asdict(replay(json.loads(Path(args.replay).read_text())))))
    else:run(json.loads(Path(args.config).read_text()),Path(args.output),Path(args.artifacts))


if __name__=='__main__':main()
