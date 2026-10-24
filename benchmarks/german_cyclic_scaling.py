"""Audit and extend source-143 German cyclic dictionary recovery, with checkpoints."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import tarfile
from time import perf_counter
import xml.etree.ElementTree as ET

from benchmarks.german_selection import build_vocabulary, normalize_form
from benchmarks.german_scaling import extension_span, length_obstructions
from benchmarks.l3_conflict import verify
from benchmarks.sample_scaling import sample_at
from voynich_smt.data.corpus import Corpus, digest, statistics, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.experiments.synthetic import generate
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

BASELINE = Path('experiments/results/german-regional-cycles-1800000ms.json')
ARTIFACTS = Path('data/generated/german-cyclic-scaling')
RESULTS = Path('experiments/results/german-cyclic-scaling')
SIZES = (23, 30, 40, 51)


def audit_o():
    with tarfile.open('data/raw/historical-lengths/german-corpus.tar.xz') as archive:
        raw = archive.extractfile('XML/143.xml').read()
    root = ET.fromstring(raw)
    parents = {child: node for node in root.iter() for child in node}
    occurrences = []
    excluded = {'bibliographie', 'annotation', 'eingriff', 'ueberschrift'}
    for morph in root.iter('morph'):
        if normalize_form(''.join(morph.itertext())) != ['o']:
            continue
        ancestry = [];node = morph
        while node in parents:
            node = parents[node];ancestry.append(node)
        if any(n.tag in excluded for n in ancestry):
            continue
        word = parents[morph]
        line = next(n for n in ancestry if n.tag == 'zeile')
        forms = [''.join(m.itertext()) for w in line.findall('wortform') for m in w.findall('morph')]
        occurrences.append({'word_number': word.get('nr'), 'line_attributes': dict(line.attrib),
                            'raw_form': ''.join(morph.itertext()), 'line_words': forms,
                            'word_xml': ET.tostring(word, encoding='unicode')})
    if not occurrences:
        raise ValueError('No non-editorial source occurrence of o')
    return {'xml_member': 'XML/143.xml', 'xml_sha256': hashlib.sha256(raw).hexdigest(),
            'occurrences': occurrences, 'conclusion': 'Separate morph o appears in source text outside excluded editorial elements; context supports an interjection. No vocabulary additions.'}


def prepare(timeout_ms=1800000, control_timeout_ms=30000):
    if any(type(n) is not int or n <= 0 for n in (timeout_ms, control_timeout_ms)):
        raise ValueError('Budgets must be positive integers')
    source = json.loads(BASELINE.read_text())
    baseline = next(r for r in source['experiments'] if r['source_id'] == 143)
    base = HiddenRecoveryRequest.from_dict(baseline['request'])
    payload = {'request': asdict(base), 'codeword_domains': 'observed'}
    if (digest(payload) != baseline['input_sha256'] or baseline['result']['status'] != 'SAT'
            or base.selection != HomophoneSelection('cycle', 'text')
            or len(base.ciphertext.words) != 22 or base.bounds.max_homophones != 2
            or base.bounds.min_code_length != 1 or base.bounds.max_code_length != 3
            or base.nulls.enabled or base.optimization.enabled):
        raise ValueError('Expected source-143 cyclic H2/L3 SAT baseline')
    verify(base, baseline['result'])
    vocabulary = build_vocabulary(143)
    if ([''.join(w) for w in base.dictionary.words] != vocabulary['words']
            or list(base.plaintext_alphabet.symbols) != vocabulary['alphabet']):
        raise ValueError('Baseline vocabulary differs from audited source')
    audit = audit_o()
    assert audit['xml_sha256'] == vocabulary['source']['xml_sha256']
    corpus = Corpus.load('data/processed/zl-eva.json')
    start, clean = extension_span(corpus, base)
    if clean < max(SIZES):
        raise ValueError('Insufficient clean extension words')
    folder = ARTIFACTS/f'budget-{timeout_ms}-controls-{control_timeout_ms}ms'
    config = {'timeout_ms': timeout_ms, 'control_timeout_ms': control_timeout_ms,
              'baseline_sha256': digest(source), 'vocabulary_sha256': digest(vocabulary),
              'corpus_sha256': corpus.identity, 'audit_sha256': digest(audit),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    report = {'schema_version': 1, 'config': config, 'config_sha256': digest(config),
              'source_id': 143, 'source_audit': audit, 'vocabulary_size': len(base.dictionary.words),
              'baseline_result': baseline['result'], 'largest_verified_sat': 22,
              'smallest_proved_unsat': None, 'minimality_proven': False,
              'prepared_inputs': [], 'experiments': [], 'complete': False,
              'semantics': 'Nested clean original prefixes, unchanged source-143 vocabulary, H2/L3 and text-wide cycling. One shared newly inferred key per complete prefix; baseline witness key not frozen. Synthetic controls share dictionary, rules and word count, not glyph lengths. No grammar or language identification claim.'}
    model = replace(base, timeout_ms=timeout_ms)
    control_pairs = [generate(replace(base, timeout_ms=control_timeout_ms), max(SIZES), seed)
                     for seed in (7, 17)]
    for size in SIZES:
        text, sample = sample_at(corpus, start, size)
        request = replace(model, ciphertext=text)
        if length_obstructions(request):
            raise ValueError('Unexpected necessary length obstruction')
        items = [(f'voynich-{size}', request, None, sample)]
        for seed, (public, full) in zip((7, 17), control_pairs):
            plain = full['plaintext']['words'][:size]
            truth = {**full, 'plaintext': {'words': plain},
                     'choices': full['choices'][:sum(map(len, plain))],
                     'generator': {**full['generator'], 'prefix_word_count': size}}
            public = replace(public, ciphertext=Text(public.ciphertext.words[:size]))
            verify(public, {'status': 'SAT', 'verified': True, 'encoder': truth['encoder'],
                            'plaintext': truth['plaintext'], 'choices': truth['choices'], 'nulls': []})
            items.append((f'control-{size}-seed-{seed}', public, truth, None))
        for name, request, truth, sample in items:
            payload = {'request': asdict(request), 'codeword_domains': 'observed'}
            path = folder/'inputs'/f'{name}.json';write_json(path, payload)
            entry = {'id': name, 'word_count': size, 'kind': 'control' if truth else 'voynich',
                     'public_input': str(path), 'input_sha256': digest(payload),
                     'statistics': statistics(request.ciphertext)}
            if truth:
                truth_path = folder/'truth'/f'{name}.json';write_json(truth_path, truth)
                entry.update(truth_path=str(truth_path), truth_sha256=digest(truth),
                             generating_witness_verified=True)
            else:
                entry['sample'] = sample
            report['prepared_inputs'].append(entry)
    return report


def update_boundary(report):
    sat = [22] + [r['word_count'] for r in report['experiments']
                  if r['kind'] == 'voynich' and r['result']['status'] == 'SAT']
    unsat = [r['word_count'] for r in report['experiments']
             if r['kind'] == 'voynich' and r['result']['status'] == 'UNSAT']
    report['largest_verified_sat'] = max(sat)
    report['smallest_proved_unsat'] = min(unsat) if unsat else None
    report['minimality_proven'] = bool(unsat) and min(unsat) == max(sat)+1
    report['unresolved_sizes'] = [n for n in SIZES if n > max(sat) and (not unsat or n < min(unsat))]


def run(timeout_ms=1800000, control_timeout_ms=30000, sizes=SIZES, solve=False, resume=False):
    if not sizes or len(set(sizes)) != len(sizes) or any(n not in SIZES for n in sizes):
        raise ValueError('Select distinct sizes from 23, 30, 40, 51')
    report = prepare(timeout_ms, control_timeout_ms)
    path = RESULTS/f'budget-{timeout_ms}-controls-{control_timeout_ms}ms.json'
    if path.exists() and resume:
        cached = json.loads(path.read_text())
        wire_inputs = json.loads(json.dumps(report['prepared_inputs']))
        if cached['config_sha256'] != report['config_sha256'] or cached['prepared_inputs'] != wire_inputs:
            raise ValueError('Resume requires identical code, budgets, corpus and prepared inputs')
        seen = set()
        for row in cached['experiments']:
            entry = next(e for e in report['prepared_inputs'] if e['id'] == row['id'])
            if row['id'] in seen or row['input_sha256'] != entry['input_sha256']:
                raise ValueError('Cached result input mismatch')
            seen.add(row['id'])
            payload = json.loads(Path(entry['public_input']).read_text())
            if digest(payload) != entry['input_sha256']:
                raise ValueError('Public input hash mismatch')
            verify(HiddenRecoveryRequest.from_dict(payload['request']), row['result'])
            if entry['kind'] == 'control' and row['result']['status'] == 'UNSAT':
                raise RuntimeError('Positive control incorrectly UNSAT')
        report['experiments'] = cached['experiments']
    elif path.exists() and (solve or json.loads(path.read_text()).get('experiments')):
        raise ValueError('Existing checkpoint: use --resume')
    update_boundary(report);write_json(path, report)
    if not solve:
        print(f'Prepared 4 nested Voynich inputs and 8 verified controls; saved {path}', flush=True)
        return report
    done = {r['id'] for r in report['experiments']}
    for size in sorted(sizes):
        if report['smallest_proved_unsat'] is not None and size >= report['smallest_proved_unsat']:
            break
        entries = [e for e in report['prepared_inputs'] if e['word_count'] == size]
        entries.sort(key=lambda e: (e['kind'] == 'voynich', e['id']))
        for entry in entries:
            if entry['id'] in done:
                continue
            payload = json.loads(Path(entry['public_input']).read_text())
            if digest(payload) != entry['input_sha256']:
                raise ValueError('Public input hash mismatch')
            request = HiddenRecoveryRequest.from_dict(payload['request'])
            print(f'{entry["id"]}: budget={request.timeout_ms}ms', flush=True)
            begin = perf_counter();result = asdict(recover_observed_codes(request));verify(request, result)
            row = {**entry, 'result': result, 'wall_seconds': perf_counter()-begin}
            report['experiments'].append(row);done.add(entry['id'])
            update_boundary(report);write_json(path, report)
            print(f'  {result["status"]}; verified={result["verified"]}; solver={result["runtime_seconds"]:.2f}s', flush=True)
            if entry['kind'] == 'control' and result['status'] == 'UNSAT':
                raise RuntimeError('Known positive control incorrectly UNSAT; stop observed testing')
    report['complete'] = all(f'voynich-{n}' in done or (
        report['smallest_proved_unsat'] is not None and n >= report['smallest_proved_unsat']) for n in SIZES)
    write_json(path, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms', type=int, default=1800000)
    parser.add_argument('--control-timeout-ms', type=int, default=30000)
    parser.add_argument('--sizes', nargs='+', type=int, choices=SIZES, default=SIZES)
    parser.add_argument('--solve', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    run(args.timeout_ms, args.control_timeout_ms, tuple(args.sizes), args.solve, args.resume)
