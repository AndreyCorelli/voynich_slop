"""Test attested contiguous German passages, rather than arbitrary dictionary words."""
import argparse
from collections import Counter, deque
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import tarfile
from time import perf_counter
import xml.etree.ElementTree as ET
import z3

from benchmarks.german_selection import build_vocabulary, normalize_form, variants
from benchmarks.historical_word_lengths import GERMAN_IDS
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import recover

ARTIFACTS = Path('data/generated/german-passages')


def extract_records(root):
    """Editorial gaps/uncertain forms break runs; ordinary page/paragraph tags do not."""
    records = []
    morph_index = 0
    def walk(node):
        nonlocal morph_index
        if node.tag in {'bibliographie', 'annotation'}:
            return
        if node.tag in {'eingriff', 'ueberschrift'}:
            records.append({'word': None, 'reason': node.tag})
            return
        if node.tag == 'wortform':
            for morph in node.findall('morph'):
                index = morph_index
                morph_index += 1
                raw_form = ''.join(morph.itertext())
                if raw_form.strip() == '§':
                    records.append({'word': None, 'reason': 'section-marker', 'morph_index': index})
                    continue
                words = normalize_form(raw_form)
                if words is None:
                    records.append({'word': None, 'reason': 'uncertain-or-number', 'morph_index': index})
                else:
                    for part, word in enumerate(words):
                        records.append({'word': word, 'morph_index': index, 'part': part})
            return
        for child in node:
            walk(child)
    walk(root)
    return records


def scan(records, cipher_lengths, bounds):
    size = len(cipher_lengths)
    if not size:
        raise ValueError('Nonempty ciphertext required')
    pending = deque(maxlen=size)
    stats = {'tokens': 0, 'barriers': 0, 'windows': 0, 'total_length_compatible': 0,
             'positionwise_length_compatible': 0, 'incompatible_windows_by_position': [0]*size}
    candidates = []
    minimum = sum((c+bounds.max_code_length-1)//bounds.max_code_length for c in cipher_lengths)
    maximum = sum(c//bounds.min_code_length for c in cipher_lengths)
    for index, record in enumerate(records):
        if record['word'] is None:
            stats['barriers'] += 1
            pending.clear()
            continue
        stats['tokens'] += 1
        pending.append((index, record))
        if len(pending) != size:
            continue
        stats['windows'] += 1
        words = [r['word'] for _, r in pending]
        lengths = list(map(len, words))
        stats['total_length_compatible'] += minimum <= sum(lengths) <= maximum
        failed = [i for i, (p, c) in enumerate(zip(lengths, cipher_lengths))
                  if not p*bounds.min_code_length <= c <= p*bounds.max_code_length]
        for i in failed:
            stats['incompatible_windows_by_position'][i] += 1
        if failed:
            continue
        stats['positionwise_length_compatible'] += 1
        candidates.append({'start_record': pending[0][0], 'end_record_exclusive': index+1,
            'source_word_locations': [{'morph_index': r['morph_index'], 'part': r['part']} for _, r in pending],
            'plaintext': words, 'plaintext_lengths': lengths})
    return stats, candidates


def solve_known(request, plaintext):
    return asdict(recover(plaintext, request.ciphertext, request.plaintext_alphabet,
        request.ciphertext_alphabet, request.bounds, request.timeout_ms,
        representation=request.representation, selection=request.selection))


def repetition_conflicts(ciphertext, words):
    """Equal ciphertext words must decode equally under a global prefix-free key."""
    if len(ciphertext.words) != len(words):
        raise ValueError('Word counts must match')
    return [{'left_word': i, 'right_word': j, 'ciphertext_word': ''.join(a),
             'left_plaintext': words[i], 'right_plaintext': words[j]}
            for i, a in enumerate(ciphertext.words) for j in range(i+1, len(words))
            if a == ciphertext.words[j] and words[i] != words[j]]


def verify_known(request, plaintext, result):
    verify(request, result)
    if result['status'] == 'SAT' and result['plaintext']['words'] != asdict(plaintext)['words']:
        if digest(result['plaintext']) != digest(asdict(plaintext)):
            raise ValueError('Known-plaintext solver returned a different passage')


def run(numbers=GERMAN_IDS, timeout_ms=30000, output=None, resume=False, prepare_only=False):
    if not numbers or len(set(numbers)) != len(numbers) or any(n not in GERMAN_IDS for n in numbers):
        raise ValueError('Expected distinct dated German sources')
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError('Timeout must be positive')
    output = Path(output or ('experiments/results/german-passages.json' if timeout_ms == 30000
                  else f'experiments/results/german-passages-{timeout_ms}ms.json'))
    baseline = json.loads(Path('experiments/results/conflict-selection.json').read_text())
    base = HiddenRecoveryRequest.from_dict(baseline['baseline_request'])
    if digest({'request': asdict(base), 'codeword_domains': 'observed'}) != baseline['baseline_input_sha256']:
        raise ValueError('Baseline request hash mismatch')
    lengths = list(map(len, base.ciphertext.words))
    requests = {}
    source_rows = []
    prepared = []
    for number in numbers:
        vocabulary = build_vocabulary(number)
        request = variants(base, vocabulary, timeout_ms)['text-cycle']
        requests[number] = request
        with tarfile.open('data/raw/historical-lengths/german-corpus.tar.xz') as archive:
            raw = archive.extractfile(f'XML/{number}.xml').read()
        if hashlib.sha256(raw).hexdigest() != vocabulary['source']['xml_sha256']:
            raise ValueError('Member hash mismatch')
        records = extract_records(ET.fromstring(raw))
        frequencies = Counter(r['word'] for r in records if r['word'] is not None)
        if dict(frequencies) != vocabulary['frequencies']:
            raise ValueError('Passage and vocabulary normalization differ')
        stats, candidates = scan(records, lengths, request.bounds)
        source_rows.append({'source_id': number, 'source': vocabulary['source'],
            'vocabulary_sha256': digest(vocabulary), 'records_sha256': digest(records), **stats})
        for candidate in candidates:
            identifier = f"{number}-record-{candidate['start_record']:06d}"
            plaintext = Text.from_string(' '.join(candidate['plaintext']))
            payload = {'mode': 'known', 'request': asdict(request), 'plaintext': asdict(plaintext)}
            prepared.append({'id': identifier, 'source_id': number, **candidate,
                'equal_ciphertext_word_conflicts': repetition_conflicts(request.ciphertext, candidate['plaintext']),
                'public_input': str(ARTIFACTS/f'budget-{timeout_ms}ms'/'inputs'/f'{identifier}.json'),
                'input_sha256': digest(payload), 'request': asdict(request)})
    config = {'sources': list(numbers), 'timeout_ms': timeout_ms, 'baseline_sha256': digest(baseline),
        'source_rows_sha256': digest(source_rows),
        'code_sha256': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
                       ('benchmarks/german_passages.py', 'benchmarks/german_selection.py',
                        'benchmarks/historical_word_lengths.py')}}
    environment = {'python': platform.python_version(), 'z3': z3.get_version_string()}
    report = {'schema_version': 1, 'config': config, 'config_sha256': digest(config),
        'environment': environment, 'sources': source_rows, 'prepared_inputs': prepared,
        'ciphertext_word_lengths': lengths, 'experiments': [], 'complete': False,
        'semantics': 'All contiguous 22-word windows within uninterrupted normalized runs in nine dated German sources. Unknown forms/editorial gaps/headings break runs. Fixed observed block, global prefix-free H2/L3, no nulls, full source alphabet and text-wide cycles. Positionwise length filter is necessary only; exact survivors are supplied as known plaintext, with attested word order. No dictionary pooling or plaintext substitutions.'}
    if resume and output.exists():
        cached = json.loads(output.read_text())
        if (cached['config_sha256'] != report['config_sha256'] or cached['environment'] != environment
                or digest(cached['prepared_inputs']) != digest(prepared)):
            raise ValueError('Resume requires identical sources, code, requests and budget')
        entries = {e['id']: e for e in prepared}
        seen = set()
        for row in cached['experiments']:
            identifier = row['id']
            if identifier in seen or identifier not in entries:
                raise ValueError('Invalid cached passage')
            seen.add(identifier)
            if digest({k: row[k] for k in entries[identifier]}) != digest(entries[identifier]):
                raise ValueError('Cached passage request mismatch')
            plain = Text.from_string(' '.join(row['plaintext']))
            verify_known(requests[row['source_id']], plain, row['result'])
        report = cached
    for entry in prepared:
        write_json(entry['public_input'], {'mode': 'known', 'request': entry['request'],
            'plaintext': asdict(Text.from_string(' '.join(entry['plaintext'])))})
    write_json(output, report)
    print(f"Scanned {sum(s['windows'] for s in source_rows)} windows; {len(prepared)} positionwise-length candidates", flush=True)
    if prepare_only:
        return report
    done = {e['id'] for e in report['experiments']}
    for entry in prepared:
        if entry['id'] in done:
            continue
        request = requests[entry['source_id']]
        plaintext = Text.from_string(' '.join(entry['plaintext']))
        begin = perf_counter()
        result = solve_known(request, plaintext)
        verify_known(request, plaintext, result)
        report['experiments'].append({**entry, 'result': result, 'wall_seconds': perf_counter()-begin})
        write_json(output, report)
        print(f"{entry['id']}: {result['status']}; solver={result['runtime_seconds']:.3f}s", flush=True)
    statuses = Counter(e['result']['status'] for e in report['experiments'])
    report['summary'] = {'windows': sum(s['windows'] for s in source_rows),
        'positionwise_length_candidates': len(prepared), 'outcomes': dict(statuses),
        'any_verified_sat': statuses['SAT'] > 0,
        'all_source_windows_excluded': statuses['UNSAT'] == len(prepared),
        'all_candidates_have_equal_ciphertext_word_conflicts': all(e['equal_ciphertext_word_conflicts'] for e in prepared),
        'all_source_windows_excluded_by_length_and_repetition_alone': all(e['equal_ciphertext_word_conflicts'] for e in prepared),
        'unsat_proofs_independently_checked': False}
    report['complete'] = True
    write_json(output, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='+', type=int, choices=GERMAN_IDS, default=GERMAN_IDS)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    parser.add_argument('--output')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    run(args.sources, args.timeout_ms, args.output, args.resume, args.prepare_only)
