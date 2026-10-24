"""Prepare a selection-only comparison against the source-143 cyclic 23-word UNSAT."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.settings import HomophoneSelection

SOURCE = Path('experiments/results/german-cyclic-scaling/budget-30000-controls-5000ms.json')
ARTIFACTS = Path('data/generated/german-free-extension')
OUTPUT = Path('experiments/results/german-free-extension.json')


def free_variant(payload):
    if set(payload) != {'request', 'codeword_domains'} or payload['codeword_domains'] != 'observed':
        raise ValueError('Observed-domain public wrapper required')
    request = HiddenRecoveryRequest.from_dict(payload['request'])
    if request.selection != HomophoneSelection('cycle', 'text'):
        raise ValueError('Text-wide cyclic source required')
    return {'request': asdict(replace(request, selection=HomophoneSelection())),
            'codeword_domains': 'observed'}


def prepare():
    source = json.loads(SOURCE.read_text())
    cyclic = next(r for r in source['experiments'] if r['id'] == 'voynich-23')
    if cyclic['result']['status'] != 'UNSAT' or source['source_id'] != 143:
        raise ValueError('Source-143 cyclic 23-word UNSAT required')
    report = {'schema_version': 1, 'source_report': str(SOURCE), 'source_sha256': digest(source),
              'analysis_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'cyclic_result': cyclic['result'], 'prepared_inputs': [], 'solver_calls': 0,
              'semantics': 'Same source-143 23-word inputs, dictionary, alphabets, H2/L3, boundaries, no nulls and solver budgets; only text-wide cycle changes to free selection. Controls reuse identical ciphertext and generating keys. Dictionary fit does not establish grammatical plaintext or manuscript language.'}
    for entry in source['prepared_inputs']:
        if entry['word_count'] != 23:
            continue
        original = json.loads(Path(entry['public_input']).read_text())
        if digest(original) != entry['input_sha256']:
            raise ValueError('Source public input hash mismatch')
        payload = free_variant(original)
        path = ARTIFACTS/'inputs'/f'{entry["id"]}-free.json'
        write_json(path, payload)
        row = {'id': entry['id']+'-free', 'kind': entry['kind'], 'public_input': str(path),
               'input_sha256': digest(payload), 'cyclic_public_input': entry['public_input'],
               'cyclic_input_sha256': digest(original), 'status': 'NOT_RUN'}
        if entry['kind'] == 'control':
            truth = json.loads(Path(entry['truth_path']).read_text())
            if digest(truth) != entry['truth_sha256']:
                raise ValueError('Control truth hash mismatch')
            verify(HiddenRecoveryRequest.from_dict(payload['request']),
                   {'status': 'SAT', 'verified': True, 'encoder': truth['encoder'],
                    'plaintext': truth['plaintext'], 'choices': truth['choices'], 'nulls': []})
            row.update(truth_path=entry['truth_path'], truth_sha256=digest(truth),
                       generating_witness_verified=True)
        report['prepared_inputs'].append(row)
    report['complete'] = True
    write_json(OUTPUT, report)
    print(f'Prepared selection-only comparison and two positive controls; saved {OUTPUT}')
    return report


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    prepare()
