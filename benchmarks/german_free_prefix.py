"""Locate the fixed German free-selection prefix boundary between 23 and 30 words."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from time import perf_counter

from benchmarks.clean_latin_prefix import boundary
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

SAT = Path('experiments/results/german-free-extension-23-30min.json')
UNSAT = Path('experiments/results/german-free-extension-30-30min.json')
OUTPUT = Path('experiments/results/german-free-prefix.json')
ARTIFACTS = Path('data/generated/german-free-prefix')


def checked_source(path, status, count):
    saved = json.loads(path.read_text())
    request = HiddenRecoveryRequest.from_dict(saved['request'])
    if (saved['result']['status'] != status or len(request.ciphertext.words) != count
            or saved['codeword_domains'] != 'observed'
            or digest({'request': asdict(request), 'codeword_domains': 'observed'}) != saved['input_sha256']):
        raise ValueError('Invalid source status, prefix length or input hash')
    verify(request, saved['result'])
    return saved, request


def run(timeout_ms=30000, resume=False, prepare_only=False):
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError('Positive integer timeout required')
    sat, lower = checked_source(SAT, 'SAT', 23)
    unsat, base = checked_source(UNSAT, 'UNSAT', 30)
    if (replace(lower, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) != base
            or base.ciphertext.words[:23] != lower.ciphertext.words):
        raise ValueError('Source results do not use one model and nested prefixes')
    report = {'schema_version': 1, 'source_sat_sha256': digest(sat), 'source_unsat_sha256': digest(unsat),
              'analysis_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'semantics': 'Only prefix length varies within the fixed source-143 free-selection H2/L3 model. Every SAT witness independently checked. UNKNOWN does not move bounds. UNSAT is solver-reported, not independently proof-checked.',
              'experiments': [], 'complete': False}
    if OUTPUT.exists():
        if not resume:
            raise ValueError('Existing checkpoint: use --resume')
        previous = json.loads(OUTPUT.read_text())
        for field in ('source_sat_sha256', 'source_unsat_sha256', 'analysis_code_sha256'):
            if previous[field] != report[field]:
                raise ValueError('Resume requires unchanged sources and analysis code')
        for row in previous['experiments']:
            request = HiddenRecoveryRequest.from_dict(row['request'])
            count = row['word_count']
            if (not 23 <= count <= 30 or request.ciphertext.words != base.ciphertext.words[:count]
                    or replace(request, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) != base
                    or digest({'request': asdict(request), 'codeword_domains': 'observed'}) != row['input_sha256']):
                raise ValueError('Cached request mismatch')
            verify(request, row['result'])
        report = previous
    else:
        for count, saved, path in ((23, sat, SAT), (30, unsat, UNSAT)):
            report['experiments'].append({'word_count': count, 'request': saved['request'],
                'input_sha256': saved['input_sha256'], 'result': saved['result'],
                'method': 'imported independently checked SAT or solver-reported UNSAT', 'source_report': str(path)})
    inputs = {}
    for count in range(24, 30):
        request = replace(base, ciphertext=Text(base.ciphertext.words[:count]), timeout_ms=timeout_ms)
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
        count = min(options, key=lambda n: (abs(n-(lo+hi)/2), n))
        request, path, checksum = inputs[count]
        report['next_input'] = str(path);write_json(OUTPUT, report)
        if prepare_only:
            return report
        print(f'Prefix {count}: SAT >= {lo}, UNSAT <= {hi}; budget={timeout_ms}ms', flush=True)
        begin = perf_counter();result = asdict(recover_observed_codes(request));verify(request, result)
        report['experiments'].append({'word_count': count, 'request': asdict(request),
            'input_sha256': checksum, 'public_input': str(path), 'result': result,
            'wall_seconds': perf_counter()-begin, 'method': 'fresh fully hidden prefix solve'})
        report['boundary'] = boundary(report['experiments']);write_json(OUTPUT, report)
        print(f'  {result["status"]}; solver={result["runtime_seconds"]:.2f}s', flush=True)
        if result['status'] == 'UNKNOWN':
            break
    report['complete'] = report['boundary']['minimality_proven']
    if report['complete']:
        report.pop('next_input', None)
    write_json(OUTPUT, report);print(json.dumps(report['boundary'], indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    run(args.timeout_ms, args.resume, args.prepare_only)
