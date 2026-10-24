"""Shrink the 29-word free-selection German conflict from its left boundary."""
import argparse
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from time import perf_counter

from benchmarks.clean_latin_prefix import boundary, truncate_witness
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

SOURCE = Path('experiments/results/german-free-prefix.json')
OUTPUT = Path('experiments/results/german-free-suffix.json')
ARTIFACTS = Path('data/generated/german-free-suffix')


def suffix_request(base, count, timeout_ms):
    if type(count) is not int or not 0 <= count <= len(base.ciphertext.words):
        raise ValueError('Invalid suffix length')
    return replace(base, ciphertext=Text(base.ciphertext.words[len(base.ciphertext.words)-count:]),
                   timeout_ms=timeout_ms)


def run(timeout_ms=30000, resume=False, prepare_only=False):
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError('Positive integer timeout required')
    source = json.loads(SOURCE.read_text())
    full = next(e for e in source['experiments'] if e['word_count'] == 29 and e['result']['status'] == 'UNSAT')
    sat = next(e for e in source['experiments'] if e['word_count'] == 28 and e['result']['status'] == 'SAT')
    base = HiddenRecoveryRequest.from_dict(full['request'])
    lower = HiddenRecoveryRequest.from_dict(sat['request'])
    for row, request in ((full, base), (sat, lower)):
        if digest({'request': asdict(request), 'codeword_domains': 'observed'}) != row['input_sha256']:
            raise ValueError('Source request hash mismatch')
        verify(request, row['result'])
    if (len(base.ciphertext.words) != 29 or lower.ciphertext.words != base.ciphertext.words[:28]
            or replace(lower, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) != base
            or base.selection.mode != 'free'):
        raise ValueError('Expected fixed free-selection 28/29 prefix boundary')
    report = {'schema_version': 1, 'source_sha256': digest(source),
              'analysis_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'semantics': 'Same source-143 free-selection H2/L3 model, contiguous suffixes ending at original word 29. New shared key per suffix, no frozen witness or phase hints. Shortest ending-at-29 suffix, not smallest arbitrary conflicting subset. UNKNOWN does not move bounds. UNSAT is solver-reported.',
              'experiments': [], 'complete': False}
    if OUTPUT.exists():
        if not resume:
            raise ValueError('Existing checkpoint: use --resume')
        cached = json.loads(OUTPUT.read_text())
        for field in ('source_sha256', 'analysis_code_sha256'):
            if cached[field] != report[field]:
                raise ValueError('Resume requires unchanged source and code')
        for row in cached['experiments']:
            request = HiddenRecoveryRequest.from_dict(row['request'])
            if (request != suffix_request(base, row['word_count'], request.timeout_ms)
                    or digest({'request': asdict(request), 'codeword_domains': 'observed'}) != row['input_sha256']):
                raise ValueError('Cached suffix request mismatch')
            verify(request, row['result'])
        report = cached
    else:
        # Existing valid key proves empty-text feasibility, not a nonempty SAT suffix.
        empty = suffix_request(base, 0, timeout_ms)
        witness = truncate_witness(sat['result'], 0)
        verify(empty, witness)
        report['experiments'] = [
            {'word_count': 0, 'start': 29, 'end': 29, 'request': asdict(empty),
             'input_sha256': digest({'request': asdict(empty), 'codeword_domains': 'observed'}),
             'result': witness, 'method': 'Existing verified key restricted to empty text; no nonempty suffix claimed SAT'},
            {'word_count': 29, 'start': 0, 'end': 29, 'request': full['request'],
             'input_sha256': full['input_sha256'], 'result': full['result'],
             'method': 'Imported full-block solver-reported UNSAT'}]
    inputs = {}
    for count in range(1, 29):
        request = suffix_request(base, count, timeout_ms)
        payload = {'request': asdict(request), 'codeword_domains': 'observed'}
        path = ARTIFACTS/f'budget-{timeout_ms}ms'/f'words-{count}.json'
        write_json(path, payload);inputs[count] = (request, path, digest(payload))
    report['boundary'] = boundary(report['experiments'])
    while not report['boundary']['minimality_proven']:
        lo = report['boundary']['largest_verified_sat'];hi = report['boundary']['smallest_proved_unsat']
        attempted = {r['word_count'] for r in report['experiments']
                     if r['result']['status'] == 'UNKNOWN' and r['request']['timeout_ms'] >= timeout_ms}
        options = [n for n in range(lo+1, hi) if n not in attempted]
        if not options:
            break
        checked_28 = any(r['word_count'] == 28 and r['result']['status'] != 'UNKNOWN'
                         for r in report['experiments'])
        count = 28 if 28 in options and not checked_28 else min(options, key=lambda n: (abs(n-(lo+hi)/2), n))
        request, path, checksum = inputs[count]
        report['next_input'] = str(path);write_json(OUTPUT, report)
        if prepare_only:
            return report
        print(f'Suffix {count} words[{29-count}:29]: SAT >= {lo}, UNSAT <= {hi}; budget={timeout_ms}ms', flush=True)
        begin = perf_counter();result = asdict(recover_observed_codes(request));verify(request, result)
        report['experiments'].append({'word_count': count, 'start': 29-count, 'end': 29,
            'request': asdict(request), 'public_input': str(path), 'input_sha256': checksum,
            'result': result, 'wall_seconds': perf_counter()-begin, 'method': 'fresh fully hidden suffix solve'})
        report['boundary'] = boundary(report['experiments']);write_json(OUTPUT, report)
        print(f'  {result["status"]}; solver={result["runtime_seconds"]:.2f}s', flush=True)
        if result['status'] == 'UNKNOWN':
            break
    report['complete'] = report['boundary']['minimality_proven']
    if report['complete']:
        report.pop('next_input', None)
        count = report['boundary']['smallest_proved_unsat']
        report['conflict'] = {'start': 29-count, 'end': 29, 'word_count': count,
                              'ciphertext_words': [''.join(w) for w in base.ciphertext.words[-count:]]}
    write_json(OUTPUT, report);print(json.dumps(report['boundary'], indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    run(args.timeout_ms, args.resume, args.prepare_only)
