"""Paired hidden and oracle-boundary recovery on a known synthetic prefix."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
from time import perf_counter
import z3
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.segmented import recover_segmented, recover_with_word_lengths


def solve_payload(payload, timeout_ms=None):
    if set(payload) not in ({'request', 'segmentation'}, {'request', 'word_lengths'}):
        raise ValueError('Expected an explicit diagnostic wrapper')
    request = HiddenRecoveryRequest.from_dict(payload['request'])
    if timeout_ms is not None: request = replace(request, timeout_ms=timeout_ms)
    if 'word_lengths' in payload:
        result = recover_with_word_lengths(request, payload['word_lengths'])
    else:
        result = request.solve() if payload['segmentation'] is None else recover_segmented(request, payload['segmentation'])
    verify(request, asdict(result))
    return result


def boundaries(truth):
    encoder = Encoder({s:tuple(tuple(c) for c in cs) for s,cs in truth['encoder']['codebook'].items()})
    choices = iter(truth['choices'])
    result = []
    for word in truth['plaintext']['words']:
        row = [0]
        for symbol in word: row.append(row[-1]+len(encoder.codebook[symbol][next(choices)]))
        result.append(row)
    return result


def run(config, output, artifacts):
    required = {'source_report','word_count','timeout_ms'}
    if (not required <= set(config) or set(config)-required-{'word_lengths_only'}
            or type(config.get('word_lengths_only',False)) is not bool
            or any(type(config[k]) is not int or config[k] <= 0 for k in ('word_count','timeout_ms'))):
        raise ValueError('Invalid segmentation diagnostic configuration')
    source = json.loads(Path(config['source_report']).read_text())
    if not source['complete']: raise ValueError('Completed prefix baseline required')
    baseline = next(r for r in source['experiments'] if r['word_count']==config['word_count'])
    public = json.loads(Path(baseline['public_input']).read_text())
    truth = json.loads(Path(baseline['truth']).read_text())
    if digest(public)!=baseline['input_sha256'] or digest(truth)!=baseline['truth_sha256']:
        raise ValueError('Source input or truth hash mismatch')
    request = HiddenRecoveryRequest.from_dict(public['request'])
    request = replace(request, timeout_ms=config['timeout_ms'])
    verify(request,dict(status='SAT',verified=True,**{k:truth[k] for k in ('encoder','plaintext','choices')}))
    segments = boundaries(truth)
    report = {'config':config,'source_sha256':digest(source),'source_input_sha256':digest(public),
        'source_truth_sha256':digest(truth),'baseline_result':baseline['result'],
        'environment':{'python':platform.python_version(),'z3':z3.get_version_string()},
        'scope':'Synthetic oracle diagnostic; full vocabulary and cipher unchanged; boundaries reveal word lengths',
        'experiments':[], 'complete':False}
    write_json(output,report)
    cases = [('boundaries',segments),('hidden',None)]
    if config.get('word_lengths_only',False):
        cases.insert(0,('lengths',[len(w) for w in truth['plaintext']['words']]))
        report['scope'] = 'Synthetic three-way diagnostic: word lengths only, exact boundaries, fully hidden'
    for mode, oracle in cases:
        payload = {'request':asdict(request), 'word_lengths' if mode=='lengths' else 'segmentation':oracle}
        path = artifacts/'inputs'/f'{mode}.json';write_json(path,payload)
        print(f'{mode}: {config["word_count"]} words, {len(request.dictionary.words)} vocabulary entries, {request.timeout_ms}ms',flush=True)
        begin=perf_counter(); result=asdict(solve_payload(payload))
        row={'mode':mode,'public_input':str(path),'input_sha256':digest(payload),
             'wall_seconds':perf_counter()-begin,'result':result}
        report['experiments'].append(row);write_json(output,report)
        print(f'  {result["status"]}: solve={result["runtime_seconds"]:.3f}s wall={row["wall_seconds"]:.3f}s',flush=True)
        if result['status']=='UNSAT':raise RuntimeError('Known positive diagnostic incorrectly UNSAT')
    report['complete']=True;write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='experiments/configs/segmentation-diagnostic.json')
    parser.add_argument('--output',default='experiments/results/segmentation-diagnostic.json')
    parser.add_argument('--artifacts',default='data/generated/segmentation-diagnostic')
    parser.add_argument('--replay')
    parser.add_argument('--timeout-ms',type=int)
    args=parser.parse_args()
    if args.timeout_ms is not None and (not args.replay or args.timeout_ms<=0):
        parser.error('--timeout-ms requires --replay and must be positive')
    if args.replay:
        print(json.dumps(asdict(solve_payload(json.loads(Path(args.replay).read_text()),args.timeout_ms))))
    else: run(json.loads(Path(args.config).read_text()),Path(args.output),Path(args.artifacts))


if __name__=='__main__':main()
