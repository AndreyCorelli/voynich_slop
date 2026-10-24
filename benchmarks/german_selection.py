"""Dated regional German vocabulary and matched free/text-cycle recovery probes."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform
import re
import tarfile
from time import perf_counter
import unicodedata as U
import xml.etree.ElementTree as ET

from benchmarks.historical_word_lengths import ABBREVIATION_MARKS, LIGATURES, SUPERSCRIPT, source
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT = Path('experiments/results/german-selection.json')
ARTIFACTS = Path('data/generated/german-selection')
NORMALIZATION_VERSION = 1


def normalize_form(value):
    """Return words, or None for an uncertain form; preserve cipher-relevant umlauts."""
    value = U.normalize('NFD', value.lower().translate(LIGATURES))
    if any(c in ABBREVIATION_MARKS for c in value) or any(c.isdigit() for c in value):
        return None
    value = value.replace('ß', 'ss').replace('`', 'er').replace("'", 'us')
    value = re.sub('([aou])\u0364', lambda m: m.group(1)+'\u0308', value)
    expanded = []
    for c in value:
        if c in SUPERSCRIPT:
            expanded.append(SUPERSCRIPT[c])
        elif c == '\u0308':
            if expanded and expanded[-1] in 'aou':
                expanded.append(c)
        elif c.isalpha():
            expanded.append(c)
        elif U.category(c).startswith('M'):
            continue
        else:
            expanded.append(' ')
    words = U.normalize('NFC', ''.join(expanded)).split()
    if any(c not in 'abcdefghijklmnopqrstuvwxyzäöü' for w in words for c in w):
        return None
    return words


def build_vocabulary(number=113):
    _, manifest = source('german-corpus.tar.xz')
    with tarfile.open('data/raw/historical-lengths/german-corpus.tar.xz') as archive:
        raw = archive.extractfile(f'XML/{number}.xml').read()
    root = ET.fromstring(raw)
    base = root.find('bibliographie/Basis')
    if base.findtext('Zeit/philnr') != 'III':
        raise ValueError('Expected period-III German witness')
    counts = Counter()
    audit = Counter()

    def walk(node):
        if node.tag in {'bibliographie', 'annotation', 'eingriff', 'ueberschrift'}:
            return
        if node.tag == 'wortform':
            for morph in node.findall('morph'):
                audit['morph_forms_seen'] += 1
                words = normalize_form(''.join(morph.itertext()))
                if words is None:
                    audit['excluded_forms'] += 1
                else:
                    counts.update(words)
            return
        for child in node:
            walk(child)
    walk(root)
    words = sorted(counts)
    if not words:
        raise ValueError('Empty German vocabulary')
    return {
        'schema_version': 1, 'normalization_version': NORMALIZATION_VERSION,
        'source': {'archive': manifest, 'xml_member': f'XML/{number}.xml',
                   'xml_sha256': hashlib.sha256(raw).hexdigest(),
                   'title': base.findtext('Titel'), 'date': base.findtext('Zeit/Jahr'),
                   'region': base.findtext('Landschaft/Sprachraum')},
        'normalization': 'Historical spelling and actual morph word divisions; lowercase; long s to s; umlaut variants unified but ä/ö/ü kept distinct; ß to ss; documented abbreviations expanded; unresolved abbreviations, digits, editorial insertions and headings excluded; no modern spelling or length-based vocabulary filtering.',
        'audit': dict(audit), 'token_count': sum(counts.values()),
        'vocabulary_size': len(words), 'words': words,
        'frequencies': dict(sorted(counts.items())),
        'alphabet': sorted(set(''.join(words))),
    }


def variants(base, vocabulary, timeout_ms):
    if (len(base.ciphertext.words) != 22 or sum(map(len, base.ciphertext.words)) != 104
            or base.bounds.max_homophones != 2 or base.bounds.min_code_length != 1
            or base.bounds.max_code_length != 3 or base.nulls.enabled or base.optimization.enabled):
        raise ValueError('Expected fixed null-free 22-word H2/L3 baseline')
    german = replace(base, dictionary=WordDictionary.from_strings(tuple(vocabulary['words'])),
                     plaintext_alphabet=Alphabet(tuple(vocabulary['alphabet'])),
                     timeout_ms=timeout_ms)
    return {'free': replace(german, selection=HomophoneSelection()),
            'text-cycle': replace(german, selection=HomophoneSelection('cycle', 'text'))}


def run(timeout_ms=30000, prepare_only=False, resume=False):
    source_path = Path('experiments/results/conflict-selection.json')
    baseline = json.loads(source_path.read_text())
    base = HiddenRecoveryRequest.from_dict(baseline['baseline_request'])
    if digest({'request': asdict(base), 'codeword_domains': 'observed'}) != baseline['baseline_input_sha256']:
        raise ValueError('Baseline request hash mismatch')
    vocabulary = build_vocabulary()
    requests = variants(base, vocabulary, timeout_ms)
    config = {'timeout_ms': timeout_ms, 'source_sha256': digest(baseline),
              'vocabulary_sha256': digest(vocabulary), 'normalization_version': NORMALIZATION_VERSION,
              'analysis_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    report = {'schema_version': 1, 'config': config, 'config_sha256': digest(config),
              'source_report': str(source_path), 'vocabulary_path': str(ARTIFACTS/'vocabulary.json'),
              'vocabulary_size': vocabulary['vocabulary_size'], 'plaintext_alphabet': vocabulary['alphabet'],
              'semantics': 'Fixed original words 2–23, H2/L3 and observed domains; dictionary and its alphabet change to one regional German corpus. Free and text-wide cycle differ only in selection. No plaintext/key hints; vocabulary membership does not establish grammatical German.',
              'prepared_inputs': [], 'experiments': [], 'complete': False,
              'environment': {'python': platform.python_version()}}
    for name, request in requests.items():
        payload = {'request': asdict(request), 'codeword_domains': 'observed'}
        graph = request.dictionary.candidate_graph(request.ciphertext, request.bounds,
                  request.min_word_length, request.max_word_length or max(map(len, request.dictionary.words)))
        report['prepared_inputs'].append({'id': name, 'public_input': str(ARTIFACTS/'inputs'/f'{name}.json'),
              'input_sha256': digest(payload), 'request': asdict(request),
              'candidate_counts_after_public_prefix_pruning': list(map(len, graph.candidates)),
              'pruned_candidates': graph.pruned_candidates})
    if resume and OUT.exists():
        cached = json.loads(OUT.read_text())
        if cached['config_sha256'] != report['config_sha256'] or digest(cached['prepared_inputs']) != digest(report['prepared_inputs']):
            raise ValueError('Resume requires identical sources, normalization, requests and budget')
        for row in cached['experiments']:
            if row['id'] not in requests or digest(row['request']) != digest(asdict(requests[row['id']])):
                raise ValueError('Cached request mismatch')
            if row['input_sha256'] != digest({'request': row['request'], 'codeword_domains': 'observed'}):
                raise ValueError('Cached input hash mismatch')
            verify(requests[row['id']], row['result'])
        report = cached
    write_json(ARTIFACTS/'vocabulary.json', vocabulary)
    for entry in report['prepared_inputs']:
        write_json(entry['public_input'], {'request': entry['request'], 'codeword_domains': 'observed'})
    write_json(OUT, report)
    if prepare_only:
        return report
    done = {row['id'] for row in report['experiments']}
    for entry in report['prepared_inputs']:
        if entry['id'] in done:
            continue
        request = requests[entry['id']]
        print(f"German {entry['id']}: vocabulary={vocabulary['vocabulary_size']}; budget={timeout_ms}ms", flush=True)
        begin = perf_counter()
        result = asdict(recover_observed_codes(request))
        verify(request, result)
        report['experiments'].append({**entry, 'result': result, 'wall_seconds': perf_counter()-begin})
        write_json(OUT, report)
        print(f"  {result['status']}; verified={result['verified']}; solver={result['runtime_seconds']:.2f}s", flush=True)
    report['complete'] = True
    write_json(OUT, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    run(args.timeout_ms, args.prepare_only, args.resume)
