"""Remove redundant repeated words, then test single deletions from the fixed conflict."""
import argparse
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from time import perf_counter

from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

SOURCE = Path('experiments/results/german-free-suffix.json')
RIGHT = Path('experiments/results/german-free-conflict-right-trim-sat.json')
OUTPUT = Path('experiments/results/german-word-deletions.json')
ARTIFACTS = Path('data/generated/german-word-deletions')


def deduplicate(request):
    if request.selection.mode != 'free' or request.nulls.enabled or request.optimization.enabled:
        raise ValueError('Duplicate equivalence requires free, null-free feasibility')
    seen = set();kept = [];removed = []
    for i, word in enumerate(request.ciphertext.words):
        if word in seen:
            removed.append(i)
        else:
            seen.add(word);kept.append(i)
    return replace(request, ciphertext=Text(tuple(request.ciphertext.words[i] for i in kept))), kept, removed


def project_witness(request, result, indices):
    """Restrict a verified free-selection witness to an ordered word subsequence."""
    if request.selection.mode != 'free':
        raise ValueError('Witness projection requires free selection')
    verify(request, result)
    if list(indices) != sorted(set(indices)) or any(i < 0 or i >= len(request.ciphertext.words) for i in indices):
        raise ValueError('Projection requires valid ordered distinct indices')
    projected = deepcopy(result)
    words = result['plaintext']['words'];offsets = [0]
    for word in words:offsets.append(offsets[-1]+len(word))
    projected['plaintext']['words'] = [words[i] for i in indices]
    projected['choices'] = [c for i in indices for c in result['choices'][offsets[i]:offsets[i+1]]]
    for field in ('segmentation', 'code_spans'):
        if result.get(field):projected[field] = [result[field][i] for i in indices]
    target = replace(request, ciphertext=Text(tuple(request.ciphertext.words[i] for i in indices)))
    verify(target, projected)
    return target, projected


def run(timeout_ms=30000, resume=False, prepare_only=False, max_solves=1):
    if type(timeout_ms) is not int or timeout_ms <= 0 or type(max_solves) is not int or max_solves < 1:
        raise ValueError('Positive integer budget and maximum solves required')
    source = json.loads(SOURCE.read_text())
    full = next(e for e in source['experiments'] if e['word_count'] == 25 and e['result']['status'] == 'UNSAT')
    base = HiddenRecoveryRequest.from_dict(full['request'])
    if digest({'request': asdict(base), 'codeword_domains': 'observed'}) != full['input_sha256']:
        raise ValueError('Source UNSAT input hash mismatch')
    unique, kept, removed = deduplicate(base)
    positions = [i+5 for i in kept]
    right = json.loads(RIGHT.read_text())
    config = {'source_sha256': digest(source), 'right_certificate_sha256': digest(right),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    report = {'schema_version': 1, 'config': config, 'config_sha256': digest(config),
              'source_words': 25, 'unique_words': len(kept), 'retained_original_positions': positions,
              'duplicate_removals_original_positions': [i+5 for i in removed],
              'base_status': 'UNSAT_BY_DUPLICATE_EQUIVALENCE',
              'base_request': asdict(unique), 'experiments': [], 'complete': False,
              'semantics': 'Same free-selection, globally prefix-free H2/L3 dictionary model. Identical complete words have identical decoded plaintext, and free choices allow copying their encodings, so duplicate copies impose no extra constraints. Fixed deduplicated base; each single-deletion request preserves remaining word order. Not an adaptive core search or minimum-cardinality core claim. UNKNOWN is unresolved. UNSAT derives from solver-reported source or fresh solver results, without independent proof certificates.'}
    if OUTPUT.exists():
        if not resume:raise ValueError('Existing checkpoint: use --resume')
        cached = json.loads(OUTPUT.read_text())
        if cached['config_sha256'] != report['config_sha256']:
            raise ValueError('Resume requires unchanged sources and code')
        report = cached
    else:
        # Deleting either endpoint was already SAT before deduplication.
        left = next(e for e in source['experiments'] if e['word_count'] == 24 and e['result']['status'] == 'SAT')
        for deleted, saved, source_positions in ((positions[0], left, list(range(6, 30))),
                                                 (positions[-1], right, list(range(5, 29)))):
            request = HiddenRecoveryRequest.from_dict(saved['request'])
            if digest({'request': asdict(request), 'codeword_domains': 'observed'}) != saved['input_sha256']:
                raise ValueError('Endpoint SAT request hash mismatch')
            wanted = [p for p in positions if p != deleted]
            target, witness = project_witness(request, saved['result'], [source_positions.index(p) for p in wanted])
            if replace(target, ciphertext=unique.ciphertext, timeout_ms=unique.timeout_ms) != unique:
                raise ValueError('Endpoint certificate changes fixed model')
            payload = {'request': asdict(target), 'codeword_domains': 'observed'}
            report['experiments'].append({'deleted_original_position': deleted,
                'remaining_original_positions': wanted, 'request': asdict(target),
                'input_sha256': digest(payload), 'result': witness,
                'method': 'Restricted independently verified endpoint SAT witness; no solver call'})
    # Validate every cached request against the original fixed deduplicated base.
    for row in report['experiments']:
        wanted = [p for p in positions if p != row['deleted_original_position']]
        q = HiddenRecoveryRequest.from_dict(row['request'])
        expected = replace(unique, ciphertext=Text(tuple(unique.ciphertext.words[positions.index(p)] for p in wanted)), timeout_ms=q.timeout_ms)
        if (row['remaining_original_positions'] != wanted or q != expected
                or digest({'request': asdict(q), 'codeword_domains': 'observed'}) != row['input_sha256']):
            raise ValueError('Cached deletion request mismatch')
        verify(q, row['result'])
    prepared = []
    for i, position in enumerate(positions):
        request = replace(unique, ciphertext=Text(unique.ciphertext.words[:i]+unique.ciphertext.words[i+1:]), timeout_ms=timeout_ms)
        payload = {'request': asdict(request), 'codeword_domains': 'observed'}
        path = ARTIFACTS/f'budget-{timeout_ms}ms'/f'delete-original-{position}.json';write_json(path, payload)
        prepared.append({'deleted_original_position': position, 'deleted_ciphertext_word': ''.join(unique.ciphertext.words[i]),
                         'remaining_original_positions': [p for p in positions if p != position],
                         'request': asdict(request), 'public_input': str(path), 'input_sha256': digest(payload)})
    report['prepared_inputs'] = prepared
    def summarize():
        status = {}
        for row in report['experiments']:
            p = row['deleted_original_position'];s = row['result']['status']
            if status.get(p) in ('SAT', 'UNSAT') and s not in (status[p], 'UNKNOWN'):
                raise RuntimeError('Contradictory deletion results')
            if status.get(p) not in ('SAT', 'UNSAT'):status[p] = s
        report['summary'] = {'necessary_words_original_positions': sorted(p for p,s in status.items() if s == 'SAT'),
                             'removable_words_original_positions': sorted(p for p,s in status.items() if s == 'UNSAT'),
                             'unresolved_original_positions': [p for p in positions if status.get(p) not in ('SAT', 'UNSAT')]}
        report['complete'] = not report['summary']['unresolved_original_positions']
        report['single_deletion_minimal'] = report['complete'] and not report['summary']['removable_words_original_positions']
    summarize();write_json(OUTPUT, report)
    if prepare_only:return report
    candidates = sorted(prepared, key=lambda e: (len(e['deleted_ciphertext_word']), e['deleted_original_position']))
    solves = 0
    for entry in candidates:
        p = entry['deleted_original_position']
        if any(r['deleted_original_position'] == p and (r['result']['status'] != 'UNKNOWN' or r['request']['timeout_ms'] >= timeout_ms) for r in report['experiments']):continue
        if solves >= max_solves:break
        report['next_input'] = entry['public_input'];write_json(OUTPUT, report)
        print(f'Delete original word {p} ({entry["deleted_ciphertext_word"]}); budget={timeout_ms}ms', flush=True)
        request = HiddenRecoveryRequest.from_dict(entry['request']);begin = perf_counter()
        result = asdict(recover_observed_codes(request));verify(request, result)
        report['experiments'].append({**entry, 'result': result, 'wall_seconds': perf_counter()-begin, 'method': 'fresh fully hidden single-deletion solve'})
        solves += 1;summarize();write_json(OUTPUT, report)
        print(f'  {result["status"]}; solver={result["runtime_seconds"]:.2f}s', flush=True)
        if result['status'] == 'UNKNOWN':break
    if report['complete']:report.pop('next_input', None)
    write_json(OUTPUT, report);print(json.dumps(report['summary'], indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    parser.add_argument('--max-solves', type=int, default=1)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    run(args.timeout_ms, args.resume, args.prepare_only, args.max_solves)
