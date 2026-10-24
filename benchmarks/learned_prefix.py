"""Check the entire prefix with proved exclusions and no pinned mappings."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
from time import perf_counter
import z3
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.learning import recover_learned


def run(config, output, artifacts):
    if (set(config) != {'source_report', 'timeout_ms', 'dictionary_encoding'}
            or type(config['timeout_ms']) is not int or config['timeout_ms'] <= 0
            or config['dictionary_encoding'] not in {'flat', 'trie'}):
        raise ValueError('Invalid learned prefix configuration')
    source = json.loads(Path(config['source_report']).read_text())
    if not source['complete'] or not source['experiments'] or not source['learned_rules']:
        raise ValueError('Completed learned search with proved rules required')
    wrapper = json.loads(Path(source['experiments'][0]['public_input']).read_text())
    if digest(wrapper) != source['experiments'][0]['input_sha256']:
        raise ValueError('Source input hash mismatch')
    context = HiddenRecoveryRequest.from_dict(wrapper['context'])
    request = replace(context, timeout_ms=config['timeout_ms'], dictionary_encoding=config['dictionary_encoding'])
    payload = {'request': asdict(request), 'context': asdict(context), 'sample_start': 0,
               'rules': source['learned_rules']}
    path = artifacts / 'inputs' / 'full-prefix.json'
    write_json(path, payload)
    report = {'config': config, 'source_sha256': digest(source), 'public_input': str(path),
        'input_sha256': digest(payload), 'word_count': len(request.ciphertext.words),
        'exclusion_counts': dict(Counter(r['kind'] for r in payload['rules'])),
        'environment': {'python': platform.python_version(), 'z3': z3.get_version_string()},
        'scope': 'Full prefix; all mappings free; only independently replayed model consequences',
        'complete': False}
    write_json(output, report)
    print(f'Full prefix: {report["word_count"]} words, {len(payload["rules"])} exclusions, '
          f'{request.timeout_ms}ms solver budget; independently validating proofs first', flush=True)
    begin = perf_counter()
    result = recover_learned(request, context, 0, payload['rules'])
    report.update(complete=True, wall_seconds=perf_counter() - begin, result=asdict(result),
        outcome={'status': result.status, 'verified': result.verified,
                 'scope': 'full fixed model', 'interpretation': {
                     'SAT': 'Verified complete plaintext and key fit',
                     'UNSAT': 'No fit for this prefix under the specified fixed model',
                     'UNKNOWN': 'Solver budget exhausted; model feasibility remains unresolved'}[result.status]})
    write_json(output, report)
    print(f'{result.status}: solver {result.runtime_seconds:.3f}s; wall {report["wall_seconds"]:.3f}s', flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='experiments/configs/learned-prefix.json')
    parser.add_argument('--output', default='experiments/results/learned-prefix.json')
    parser.add_argument('--artifacts', default='data/generated/learned-prefix')
    args = parser.parse_args()
    run(json.loads(Path(args.config).read_text()), Path(args.output), Path(args.artifacts))


if __name__ == '__main__':
    main()
