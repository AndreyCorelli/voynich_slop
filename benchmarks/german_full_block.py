"""Restore the contiguous 30-word block using a verified surviving German vocabulary."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest

ROBUSTNESS = Path('experiments/results/german-vocabulary-robustness/budget-1800000ms.json')
FULL = Path('experiments/results/german-free-extension-30-30min.json')
POSITIONS = Path('experiments/results/german-word-deletions-joint-preparation.json')
ARTIFACTS = Path('data/generated/german-vocabulary-robustness/full-block')
OUTPUT = Path('experiments/results/german-vocabulary-full-block-preparation.json')


def prepare(source_id=133, timeout_ms=30000):
    if source_id not in (123, 133, 153, 233) or type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError('Select a surviving vocabulary and positive integer budget')
    source = json.loads(ROBUSTNESS.read_text())
    entry = next(e for e in source['experiments'] if e['source_id'] == source_id)
    payload = json.loads(Path(entry['public_input']).read_text())
    if digest(payload) != entry['input_sha256'] or entry['result']['status'] != 'SAT':
        raise ValueError('Verified surviving subset result required')
    base = HiddenRecoveryRequest.from_dict(payload['request']);verify(base, entry['result'])
    full = json.loads(FULL.read_text());model = HiddenRecoveryRequest.from_dict(full['request'])
    if len(model.ciphertext.words) != 30:
        raise ValueError('Expected full 30-word block')
    positions = json.loads(POSITIONS.read_text())['remaining_original_positions']
    if tuple(model.ciphertext.words[i-1] for i in positions) != base.ciphertext.words:
        raise ValueError('Full block does not contain verified subset in original order')
    request = replace(base, ciphertext=model.ciphertext, timeout_ms=timeout_ms)
    if replace(request, dictionary=model.dictionary, plaintext_alphabet=model.plaintext_alphabet,
               timeout_ms=model.timeout_ms) != model:
        raise ValueError('Full block changes cipher settings')
    public = {'request': asdict(request), 'codeword_domains': 'observed'}
    path = ARTIFACTS/f'{source_id}-words-30.json';write_json(path, public)
    report = {'source_id': source_id, 'word_count': 30, 'public_input': str(path),
              'input_sha256': digest(public), 'verified_subset_result_sha256': digest(entry),
              'subset_original_positions': positions, 'full_block_result_sha256': digest(full),
              'semantics': 'Restore full contiguous original 30-word block with one surviving regional vocabulary; unchanged free-selection H2/L3 and remaining settings. One newly inferred global key; no fixed subset witness key or plaintext hints.',
              'solver_calls': 0, 'status': 'NOT_RUN'}
    write_json(OUTPUT, report);print(f'Prepared source {source_id}, full 30-word block; saved {OUTPUT}')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=int, choices=(123, 133, 153, 233), default=133)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    args = parser.parse_args()
    prepare(args.source, args.timeout_ms)
