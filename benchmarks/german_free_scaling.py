"""Prepare nested 30/40/51-word free-selection probes beyond verified SAT at 23."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from benchmarks.german_free_extension import free_variant
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest

SOURCE = Path('experiments/results/german-cyclic-scaling/budget-1800000-controls-30000ms.json')
SAT = Path('experiments/results/german-free-extension-23-30min.json')
ARTIFACTS = Path('data/generated/german-free-extension')
OUTPUT = Path('experiments/results/german-free-scaling-preparation.json')


def prepare(timeout_ms=30000):
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError('Budget must be a positive integer')
    source = json.loads(SOURCE.read_text());sat = json.loads(SAT.read_text())
    base = HiddenRecoveryRequest.from_dict(sat['request'])
    if sat['result']['status'] != 'SAT' or len(base.ciphertext.words) != 23:
        raise ValueError('Verified 23-word SAT result required')
    if digest({'request': asdict(base), 'codeword_domains': 'observed'}) != sat['input_sha256']:
        raise ValueError('SAT request hash mismatch')
    verify(base, sat['result'])
    report = {'source_sha256': digest(source), 'sat_prefix_result_sha256': digest(sat),
              'verified_sat_prefix_words': 23, 'prepared_inputs': [], 'solver_calls': 0,
              'semantics': 'Unchanged source-143 free-selection H2/L3 model. Each 30/40/51-word prefix uses one newly inferred shared key; no frozen baseline key. Controls reuse cyclic generating witnesses and ciphertext, matching word counts and model, not Voynich glyph lengths.'}
    for entry in source['prepared_inputs']:
        if entry['word_count'] not in (30, 40, 51):
            continue
        old = json.loads(Path(entry['public_input']).read_text())
        if digest(old) != entry['input_sha256']:
            raise ValueError('Source request hash mismatch')
        public = free_variant(old)
        request = replace(HiddenRecoveryRequest.from_dict(public['request']), timeout_ms=timeout_ms)
        if replace(request, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) != base:
            raise ValueError('Extension changes the verified prefix model')
        if entry['kind'] == 'voynich' and request.ciphertext.words[:23] != base.ciphertext.words:
            raise ValueError('Extension is not nested')
        public = {'request': asdict(request), 'codeword_domains': 'observed'}
        path = ARTIFACTS/'inputs'/f'{entry["id"]}-free.json'
        write_json(path, public)
        row = {**entry, 'id': entry['id']+'-free', 'cyclic_public_input': entry['public_input'],
               'cyclic_input_sha256': entry['input_sha256'], 'public_input': str(path),
               'input_sha256': digest(public), 'status': 'NOT_RUN'}
        if entry['kind'] == 'control':
            truth = json.loads(Path(entry['truth_path']).read_text())
            if digest(truth) != entry['truth_sha256']:
                raise ValueError('Control truth hash mismatch')
            verify(request, {'status': 'SAT', 'verified': True, 'encoder': truth['encoder'],
                             'plaintext': truth['plaintext'], 'choices': truth['choices'], 'nulls': []})
        report['prepared_inputs'].append(row)
    write_json(OUTPUT, report)
    print(f'Prepared three nested free-selection targets and six verified controls; saved {OUTPUT}')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    args = parser.parse_args()
    prepare(args.timeout_ms)
