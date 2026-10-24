"""Test the fixed 19-word free-selection conflict against individual German vocabularies."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from time import perf_counter

from benchmarks.german_scaling import length_obstructions
from benchmarks.german_selection import build_vocabulary
from benchmarks.historical_word_lengths import GERMAN_IDS
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.solver.observed_codes import recover_observed_codes

SOURCES = tuple(n for n in GERMAN_IDS if n != 143)
BASELINE = Path('experiments/results/german-word-deletions-joint-30min.json')
ARTIFACTS = Path('data/generated/german-vocabulary-robustness')
RESULTS = Path('experiments/results/german-vocabulary-robustness')


def regional_request(base, vocabulary, timeout_ms):
    if (len(base.ciphertext.words) != 19 or base.selection != HomophoneSelection()
            or base.bounds.max_homophones != 2 or base.bounds.min_code_length != 1
            or base.bounds.max_code_length != 3 or base.nulls.enabled or base.optimization.enabled):
        raise ValueError('Expected fixed free-selection 19-word H2/L3 conflict')
    return replace(base, dictionary=WordDictionary.from_strings(tuple(vocabulary['words'])),
                   plaintext_alphabet=Alphabet(tuple(vocabulary['alphabet'])), timeout_ms=timeout_ms)


def run(timeout_ms=30000, numbers=SOURCES, resume=False, prepare_only=False):
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError('Positive integer budget required')
    if not numbers or len(set(numbers)) != len(numbers) or any(n not in SOURCES for n in numbers):
        raise ValueError('Select distinct other German source identifiers')
    baseline = json.loads(BASELINE.read_text())
    base = HiddenRecoveryRequest.from_dict(baseline['request'])
    if (baseline['codeword_domains'] != 'observed' or baseline['result']['status'] != 'UNSAT'
            or digest({'request': asdict(base), 'codeword_domains': 'observed'}) != baseline['input_sha256']):
        raise ValueError('Invalid baseline result or request hash')
    old = build_vocabulary(143)
    if regional_request(base, old, base.timeout_ms) != base:
        raise ValueError('Baseline differs from source-143 vocabulary')
    vocabularies = {n: build_vocabulary(n) for n in numbers}
    config = {'sources': list(numbers), 'timeout_ms': timeout_ms,
              'baseline_sha256': digest(baseline), 'vocabulary_sha256': {str(n): digest(v) for n,v in vocabularies.items()},
              'code_sha256': {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in
                  ('benchmarks/german_vocabulary_robustness.py', 'benchmarks/german_selection.py')}}
    report = {'schema_version': 1, 'config': config, 'config_sha256': digest(config),
              'baseline_source_id': 143, 'baseline_result': baseline['result'],
              'prepared_inputs': [], 'experiments': [], 'complete': False,
              'semantics': 'Same fixed 19-word noncontiguous conflict, free selection, global prefix-free H2/L3, preserved word boundaries, no nulls or contractions. Each regional dictionary separately; only dictionary, plaintext alphabet and timeout change. Full source vocabularies, no pooling or length/frequency filtering. UNSAT_BY_LENGTH is a direct necessary-condition certificate; UNSAT is solver-reported. UNKNOWN is unresolved. SAT means dictionary compatibility, not grammatical prose or manuscript-language identification.'}
    folder = ARTIFACTS/f'budget-{timeout_ms}ms'
    for n,v in vocabularies.items():
        q = regional_request(base, v, timeout_ms)
        payload = {'request': asdict(q), 'codeword_domains': 'observed'}
        path = folder/'inputs'/f'{n}.json';write_json(path, payload)
        write_json(ARTIFACTS/'vocabularies'/f'{n}.json', v)
        report['prepared_inputs'].append({'source_id': n, 'public_input': str(path),
            'input_sha256': digest(payload), 'vocabulary_size': v['vocabulary_size'],
            'source': v['source'], 'one_letter_words': [w for w in v['words'] if len(w) == 1],
            'length_obstructions': length_obstructions(q)})
    output = RESULTS/f'budget-{timeout_ms}ms.json'
    if output.exists():
        if not resume:raise ValueError('Existing checkpoint: use --resume')
        cached = json.loads(output.read_text())
        if cached['config_sha256'] != report['config_sha256'] or cached['prepared_inputs'] != report['prepared_inputs']:
            raise ValueError('Resume requires unchanged budgets, sources, code and inputs')
        seen = set()
        for row in cached['experiments']:
            n = row['source_id']
            if n in seen:raise ValueError('Duplicate cached source')
            seen.add(n)
            entry = next(e for e in report['prepared_inputs'] if e['source_id'] == n)
            payload = json.loads(Path(entry['public_input']).read_text())
            if digest(payload) != row['input_sha256'] or row['input_sha256'] != entry['input_sha256']:
                raise ValueError('Cached request hash mismatch')
            q = HiddenRecoveryRequest.from_dict(payload['request'])
            if row['result']['status'] == 'UNSAT_BY_LENGTH':
                if not length_obstructions(q) or row['length_obstructions'] != length_obstructions(q):
                    raise ValueError('Cached length certificate mismatch')
            else:verify(q, row['result'])
        report['experiments'] = cached['experiments']
    write_json(output, report)
    if prepare_only:
        print(f'Prepared {len(numbers)} individual vocabulary probes; saved {output}', flush=True)
        return report
    done = {e['source_id'] for e in report['experiments']}
    for entry in report['prepared_inputs']:
        if entry['source_id'] in done:continue
        payload = json.loads(Path(entry['public_input']).read_text())
        if digest(payload) != entry['input_sha256']:raise ValueError('Public input hash mismatch')
        q = HiddenRecoveryRequest.from_dict(payload['request'])
        print(f'German {entry["source_id"]}: vocabulary={entry["vocabulary_size"]}; budget={timeout_ms}ms', flush=True)
        begin = perf_counter()
        if entry['length_obstructions']:
            result = {'status': 'UNSAT_BY_LENGTH', 'verified': False, 'runtime_seconds': 0}
            solver_run = False
        else:
            result = asdict(recover_observed_codes(q));verify(q, result);solver_run = True
        report['experiments'].append({**entry, 'result': result, 'solver_run': solver_run,
                                     'wall_seconds': perf_counter()-begin})
        write_json(output, report)
        print(f'  {result["status"]}; solver={result["runtime_seconds"]:.2f}s', flush=True)
    report['complete'] = True
    report['summary'] = {s: [r['source_id'] for r in report['experiments'] if r['result']['status'] == s]
                         for s in ('SAT', 'UNSAT', 'UNSAT_BY_LENGTH', 'UNKNOWN')}
    write_json(output, report);print(json.dumps(report['summary'], indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    parser.add_argument('--sources', nargs='+', type=int, choices=SOURCES, default=SOURCES)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    run(args.timeout_ms, tuple(args.sources), args.resume, args.prepare_only)
