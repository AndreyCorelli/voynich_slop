"""Checkpoint text-wide cyclic probes for the other eight dated German sources."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
from time import perf_counter
import z3

from benchmarks.german_selection import build_vocabulary, variants
from benchmarks.historical_word_lengths import GERMAN_IDS
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.observed_codes import recover_observed_codes

SOURCES = tuple(n for n in GERMAN_IDS if n != 113)
ARTIFACTS = Path('data/generated/german-regional-cycles')


def run(numbers=SOURCES, timeout_ms=30000, output=None, resume=False, prepare_only=False):
    if not numbers or len(set(numbers)) != len(numbers) or any(n not in SOURCES for n in numbers):
        raise ValueError('Expected distinct selected sources from the other eight period-III witnesses')
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError('Timeout must be positive')
    output = Path(output or ('experiments/results/german-regional-cycles.json' if timeout_ms == 30000
                   else f'experiments/results/german-regional-cycles-{timeout_ms}ms.json'))
    baseline_path = Path('experiments/results/conflict-selection.json')
    baseline = json.loads(baseline_path.read_text())
    base = HiddenRecoveryRequest.from_dict(baseline['baseline_request'])
    if digest({'request': asdict(base), 'codeword_domains': 'observed'}) != baseline['baseline_input_sha256']:
        raise ValueError('Baseline hash mismatch')
    vocabularies = {number: build_vocabulary(number) for number in numbers}
    requests = {number: variants(base, vocabularies[number], timeout_ms)['text-cycle'] for number in numbers}
    config = {'sources': list(numbers), 'timeout_ms': timeout_ms, 'baseline_sha256': digest(baseline),
              'vocabulary_sha256': {str(n): digest(vocabularies[n]) for n in numbers},
              'code_sha256': {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in
                              ('benchmarks/german_regional_cycles.py', 'benchmarks/german_selection.py')}}
    environment = {'python': platform.python_version(), 'z3': z3.get_version_string()}
    report = {'schema_version': 1, 'config': config, 'config_sha256': digest(config),
              'environment': environment, 'baseline_report': str(baseline_path),
              'semantics': 'Each regional vocabulary individually; fixed original words 2–23, H2/L3, no nulls, trie dictionary, observed code domains and text-wide cycling. Only vocabulary, its alphabet and timeout change. No pooling, plaintext hints or frequency/length filtering.',
              'prepared_inputs': [], 'experiments': [], 'complete': False}
    for number, request in requests.items():
        vocabulary = vocabularies[number]
        graph = request.dictionary.candidate_graph(request.ciphertext, request.bounds,
                request.min_word_length, request.max_word_length or max(map(len, request.dictionary.words)))
        payload = {'request': asdict(request), 'codeword_domains': 'observed'}
        report['prepared_inputs'].append({'source_id': number,
            'public_input': str(ARTIFACTS/f'budget-{timeout_ms}ms'/'inputs'/f'{number}.json'),
            'input_sha256': digest(payload), 'request': asdict(request),
            'vocabulary_path': str(ARTIFACTS/'vocabularies'/f'{number}.json'),
            'vocabulary_size': vocabulary['vocabulary_size'], 'token_count': vocabulary['token_count'],
            'source': vocabulary['source'], 'audit': vocabulary['audit'],
            'candidate_counts': list(map(len, graph.candidates)), 'pruned_candidates': graph.pruned_candidates})
    if resume and output.exists():
        cached = json.loads(output.read_text())
        if (cached['config_sha256'] != report['config_sha256'] or cached['environment'] != environment
                or digest(cached['prepared_inputs']) != digest(report['prepared_inputs'])):
            raise ValueError('Resume requires identical sources, code, environment and budget')
        seen = set()
        for row in cached['experiments']:
            number = row['source_id']
            if number in seen or number not in requests:
                raise ValueError('Invalid cached source')
            seen.add(number)
            payload = {'request': row['request'], 'codeword_domains': 'observed'}
            if (digest(row['request']) != digest(asdict(requests[number]))
                    or digest(payload) != row['input_sha256']):
                raise ValueError('Cached request hash mismatch')
            verify(requests[number], row['result'])
        report = cached
    for entry in report['prepared_inputs']:
        write_json(entry['vocabulary_path'], vocabularies[entry['source_id']])
        write_json(entry['public_input'], {'request': entry['request'], 'codeword_domains': 'observed'})
    write_json(output, report)
    if prepare_only:
        return report
    done = {row['source_id'] for row in report['experiments']}
    for entry in report['prepared_inputs']:
        number = entry['source_id']
        if number in done:
            continue
        request = requests[number]
        print(f"German {number}: words={entry['vocabulary_size']}; budget={timeout_ms}ms", flush=True)
        begin = perf_counter()
        result = asdict(recover_observed_codes(request))
        verify(request, result)
        report['experiments'].append({**entry, 'result': result, 'wall_seconds': perf_counter()-begin})
        write_json(output, report)
        print(f"  {result['status']}; verified={result['verified']}; solver={result['runtime_seconds']:.2f}s", flush=True)
    report['complete'] = True
    write_json(output, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='+', type=int, choices=SOURCES, default=SOURCES)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    parser.add_argument('--output')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    run(args.sources, args.timeout_ms, args.output, args.resume, args.prepare_only)
