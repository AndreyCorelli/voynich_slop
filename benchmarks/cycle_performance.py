"""Paired cycle-formula timing and full-vocabulary positive controls."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
import random
import sys
from time import perf_counter
import z3
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.recovery import _recover


def solve(request, mode):
    return _recover(None, request.ciphertext, request.plaintext_alphabet,
        request.ciphertext_alphabet, request.bounds, request.timeout_ms,
        dictionary=request.dictionary, min_word_length=request.min_word_length,
        max_word_length=request.max_word_length or max(map(len, request.dictionary.words)),
        representation=request.representation, selection=request.selection,
        dictionary_encoding=request.dictionary_encoding, cycle_encoding=mode)


def reduced(request, truth, size, seed):
    """Declared easier controls include truth words, without supplying their order."""
    required = {tuple(w) for w in truth['plaintext']['words']}
    if size < len(required) or size > len(request.dictionary.words):
        raise ValueError('Invalid calibration vocabulary size')
    others = [w for w in request.dictionary.words if w not in required]
    chosen = required | set(random.Random(seed).sample(others, size-len(required)))
    return replace(request, dictionary=WordDictionary(tuple(w for w in request.dictionary.words if w in chosen)))


def run(config, output, artifacts):
    required = {'source_report', 'seeds', 'vocabulary_sizes', 'control_timeout_ms', 'prefix_timeout_ms'}
    if (set(config) != required or not config['seeds']
            or any(type(s) is not int for s in config['seeds'])
            or len(set(config['seeds'])) != len(config['seeds'])
            or any(type(n) is not int or n <= 0 for n in config['vocabulary_sizes'])
            or len(set(config['vocabulary_sizes'])) != len(config['vocabulary_sizes'])
            or any(type(config[k]) is not int or config[k] <= 0
                   for k in ('control_timeout_ms', 'prefix_timeout_ms'))):
        raise ValueError('Invalid cycle performance configuration')
    source = json.loads(Path(config['source_report']).read_text())
    report = {'config': config, 'source_sha256': digest(source), 'experiments': [], 'complete': False,
        'environment': {'python': platform.python_version(), 'z3': z3.get_version_string()},
        'implementation_sha256': {str(p): digest(p.read_text()) for p in
            (Path('src/voynich_smt/solver/recovery.py'), Path('src/voynich_smt/solver/selection.py'))},
        'semantics': 'Hidden solve receives no truth; reduced vocabularies are declared easier positive controls'}
    write_json(output, report)
    for seed in config['seeds']:
        row = next(e for e in source['experiments'] if e['id'] == f'full-hidden-{seed}')
        original = HiddenRecoveryRequest.from_dict(json.loads(Path(row['public_input']).read_text()))
        truth = json.loads(Path(row['truth']).read_text())
        verify(original, dict(status='SAT', verified=True, **{k:truth[k] for k in ('encoder','plaintext','choices')}))
        sizes = config['vocabulary_sizes'] + [len(original.dictionary.words)] if seed == config['seeds'][0] else [len(original.dictionary.words)]
        for size in sizes:
            request = replace(original, timeout_ms=config['control_timeout_ms'], dictionary_encoding='trie')
            if size < len(original.dictionary.words): request = reduced(request, truth, size, seed)
            modes = ['history', 'state'] if seed == config['seeds'][0] else ['state']
            for mode in modes:
                name = f'seed-{seed}-vocab-{size}-{mode}'
                payload = {'request': asdict(request), 'cycle_encoding': mode}
                path = artifacts / 'inputs' / f'{name}.json'; write_json(path, payload)
                print(name, flush=True)
                begin = perf_counter(); reused = None
                probe = Path(f'experiments/results/cycle-{mode}-probe.json')
                if seed == 7 and size == len(original.dictionary.words) and probe.exists():
                    prior = json.loads(probe.read_text())
                    if digest(prior['request']) == digest(asdict(request)):
                        result = prior['result']; wall = prior['wall_seconds']; reused = str(probe)
                    else: result = asdict(solve(request, mode)); wall = perf_counter()-begin
                else: result = asdict(solve(request, mode)); wall = perf_counter()-begin
                verify(request, result)
                if result['status'] == 'UNSAT': raise RuntimeError('Known positive control returned UNSAT')
                report['experiments'].append({'id':name,'public_input':str(path),'input_sha256':digest(payload),
                    'truth':row['truth'],'vocabulary_size':size,'seed':seed,'cycle_encoding':mode,
                    'wall_seconds':wall,'reused_from':reused,'result':result})
                write_json(output, report)
                print(f'  {result["status"]}: solve={result["runtime_seconds"]:.3f}s wall={wall:.3f}s',flush=True)
    prefix = next(e for e in source['experiments'] if e['id'] == source['prefix']['experiment_id'])
    request = HiddenRecoveryRequest.from_dict(json.loads(Path(prefix['public_input']).read_text()))
    request = replace(request, timeout_ms=config['prefix_timeout_ms'], dictionary_encoding='trie')
    payload = {'request':asdict(request),'cycle_encoding':'state'}
    path = artifacts/'inputs'/'voynich-prefix-state.json'; write_json(path,payload)
    print('Voynich full prefix, state cycles, no pins/exclusions',flush=True)
    begin = perf_counter(); result = asdict(solve(request, 'state')); verify(request,result)
    report['prefix'] = {'public_input':str(path),'input_sha256':digest(payload),'wall_seconds':perf_counter()-begin,
                        'result':result,'scope':'Full unchanged model, no pins or learned clauses'}
    report['complete']=True; write_json(output,report)
    print('Prefix '+result['status'],flush=True)
    return report



def replay(payload, timeout_ms=None):
    """Replay an exact public case, optionally changing only its solve budget."""
    request = HiddenRecoveryRequest.from_dict(payload['request'])
    if timeout_ms is not None:
        if type(timeout_ms) is not int or timeout_ms <= 0:
            raise ValueError('Replay timeout must be a positive integer')
        request = replace(request, timeout_ms=timeout_ms)
    actual = {'request': asdict(request), 'cycle_encoding': payload['cycle_encoding']}
    begin = perf_counter()
    result = asdict(solve(request, payload['cycle_encoding']))
    verify(request, result)
    return {**actual, 'input_sha256': digest(actual), 'wall_seconds': perf_counter()-begin,
            'environment': {'python': platform.python_version(), 'z3': z3.get_version_string()},
            'result': result, 'complete': True}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='experiments/configs/cycle-performance.json')
    parser.add_argument('--output',default='experiments/results/cycle-performance.json')
    parser.add_argument('--artifacts',default='data/generated/cycle-performance')
    parser.add_argument('--replay')
    parser.add_argument('--timeout-ms', type=int, help='Override only the replay solver budget')
    parser.add_argument('--replay-output', help='Save the replay request, result and timing as JSON')
    args=parser.parse_args()
    if (args.timeout_ms is not None or args.replay_output) and not args.replay:
        parser.error('--timeout-ms and --replay-output require --replay')
    if args.timeout_ms is not None and args.timeout_ms <= 0:
        parser.error('--timeout-ms must be positive')
    if args.replay:
        payload=json.loads(Path(args.replay).read_text())
        budget = args.timeout_ms or payload['request']['timeout_ms']
        print(f'Replaying {args.replay}; solver budget {budget}ms', file=sys.stderr, flush=True)
        report = replay(payload, args.timeout_ms)
        if args.replay_output:
            write_json(Path(args.replay_output), report)
            result = report['result']
            print(f'{result["status"]}; verified={result["verified"]}; '
                  f'solver={result["runtime_seconds"]:.2f}s; saved {args.replay_output}', flush=True)
        else:
            print(json.dumps(report['result']))
    else: run(json.loads(Path(args.config).read_text()),Path(args.output),Path(args.artifacts))


if __name__=='__main__': main()
