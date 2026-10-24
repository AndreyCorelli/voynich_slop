"""Prepare fixed German prefix probes and certify elementary length obstructions."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

from benchmarks.l3_conflict import verify
from benchmarks.sample_scaling import sample_at
from voynich_smt.data.corpus import Corpus, digest, statistics, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.experiments.synthetic import generate
from voynich_smt.models.settings import HomophoneSelection

ARTIFACTS = Path('data/generated/german-scaling')
OUTPUT = Path('experiments/results/german-scaling.json')
BASELINE = Path('experiments/results/german-selection-free-30min.json')
CORPUS = Path('data/processed/zl-eva.json')


def length_obstructions(request):
    """Certify words impossible even before requiring a shared prefix-free key."""
    if request.nulls.enabled:
        raise ValueError('Length certificates require a null-free model')
    words = [w for w in request.dictionary.words
             if request.min_word_length <= len(w) <= (
                 request.max_word_length or max(map(len, request.dictionary.words)))]
    if not words:
        raise ValueError('No admissible dictionary words')
    sizes = sorted(set(map(len, words)))
    result = []
    for position, word in enumerate(request.ciphertext.words, 1):
        compatible = [n for n in sizes if
                      n * request.bounds.min_code_length <= len(word)
                      <= n * request.bounds.max_code_length]
        if not compatible:
            result.append({'position': position, 'ciphertext_word': ''.join(word),
                           'ciphertext_length': len(word), 'admissible_plaintext_lengths': sizes,
                           'min_code_length': request.bounds.min_code_length,
                           'max_code_length': request.bounds.max_code_length,
                           'certificate': 'No admissible plaintext length can emit this ciphertext length.'})
    return result


def extension_span(corpus, base, maximum=60):
    matches = [i for i in range(len(corpus.records)-len(base.ciphertext.words)+1)
               if tuple(tuple(r['tokens']) for r in corpus.records[i:i+len(base.ciphertext.words)])
               == base.ciphertext.words]
    if len(matches) != 1:
        raise ValueError('Expected one exact occurrence of the baseline block')
    start = matches[0]
    folio = corpus.records[start].get('folio')
    usable = 0
    for record in corpus.records[start:start+maximum]:
        locator = record.get('locus', '').partition(',')[2]
        if (not record['tokens'] or record.get('uncertain_space_in_locus', False)
                or record.get('folio') != folio or not locator[1:].startswith('P')
                or any(g not in base.ciphertext_alphabet.symbols for g in record['tokens'])):
            break
        usable += 1
    if usable < len(base.ciphertext.words):
        raise ValueError('Baseline is not an uninterrupted clean paragraph sample')
    return start, usable


def run(timeout_ms=1800000):
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError('Timeout must be positive')
    baseline = json.loads(BASELINE.read_text())
    base = HiddenRecoveryRequest.from_dict(baseline['request'])
    if (baseline['codeword_domains'] != 'observed'
            or digest({'request': asdict(base), 'codeword_domains': 'observed'}) != baseline['input_sha256']
            or baseline['result']['status'] != 'SAT' or len(base.ciphertext.words) != 22
            or base.bounds.max_homophones != 2 or base.bounds.min_code_length != 1
            or base.bounds.max_code_length != 3 or base.nulls.enabled or base.optimization.enabled
            or base.selection != HomophoneSelection()):
        raise ValueError('Expected verified original free-selection German H2/L3 baseline')
    verify(base, baseline['result'])
    corpus = Corpus.load(CORPUS)
    start, usable = extension_span(corpus, base)
    sizes = sorted({22, 23, *(min(n, usable) for n in (30, 40, 60))})
    model = replace(base, timeout_ms=timeout_ms)
    report = {'schema_version': 1, 'baseline_path': str(BASELINE), 'baseline_sha256': digest(baseline),
              'corpus_sha256': corpus.identity, 'analysis_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'requested_sizes': [30, 40, 60], 'effective_sizes': sizes,
              'clean_prefix_words': usable, 'first_excluded_record': start+usable,
              'vocabulary_size': len(base.dictionary.words),
              'minimum_dictionary_word_length': min(map(len, base.dictionary.words)),
              'timeout_ms': timeout_ms, 'experiments': [], 'controls': [], 'solver_calls': 0,
              'semantics': 'Identical German vocabulary, alphabet, H2/L3, free selection, no nulls, no contractions, and preserved boundaries. Each request infers one shared key for its entire nested prefix; the 22-word witness key is not frozen. Offline length certificates are separate from SMT results.'}
    for size in sizes:
        text, metadata = sample_at(corpus, start, size)
        request = replace(model, ciphertext=text)
        assert text.words[:22] == base.ciphertext.words
        payload = {'request': asdict(request), 'codeword_domains': 'observed'}
        path = ARTIFACTS/'inputs'/f'voynich-{size}.json'
        write_json(path, payload)
        proofs = length_obstructions(request)
        row = {'word_count': size, 'public_input': str(path), 'input_sha256': digest(payload),
               'sample': metadata, 'statistics': statistics(text), 'length_obstructions': proofs,
               'status': 'UNSAT_BY_LENGTH' if proofs else ('SAT' if size == 22 else 'NOT_RUN'),
               'solver_run': False}
        if size == 22:
            row['verified_baseline_result'] = baseline['result']
        report['experiments'].append(row)
    first = next((row for row in report['experiments'] if row['word_count'] == 23
                  and row['length_obstructions']), None)
    report['boundary'] = {'largest_verified_sat': 22, 'smallest_proved_unsat': 23 if first else None,
                          'minimality_proven': first is not None,
                          'proof_kind': 'ordinary-Python necessary emission-length certificate',
                          'unresolved_sizes': [] if first else [n for n in sizes if n > 22]}
    # Controls are independently generated, with all hidden truth in separate files.
    # Exact glyph-length matching is impossible here: the target contains a one-character word.
    for size in sorted(set(sizes)-{22, 23}):
        for seed in (7, 17):
            public, truth = generate(model, usable, seed)
            plain_words = truth['plaintext']['words'][:size]
            choices = truth['choices'][:sum(map(len, plain_words))]
            public = replace(public, ciphertext=type(public.ciphertext)(public.ciphertext.words[:size]))
            truth = {**truth, 'plaintext': {'words': plain_words}, 'choices': choices,
                     'generator': {**truth['generator'], 'parent_word_count': usable,
                                   'prefix_word_count': size}}
            verify(public, {'status': 'SAT', 'verified': True, 'encoder': truth['encoder'],
                            'plaintext': truth['plaintext'], 'choices': truth['choices'], 'nulls': []})
            payload = {'request': asdict(public), 'codeword_domains': 'observed'}
            name = f'control-{size}-seed-{seed}'
            path = ARTIFACTS/'inputs'/f'{name}.json';truth_path = ARTIFACTS/'truth'/f'{name}.json'
            write_json(path, payload);write_json(truth_path, truth)
            report['controls'].append({'word_count': size, 'seed': seed, 'public_input': str(path),
                                      'input_sha256': digest(payload), 'truth_path': str(truth_path),
                                      'truth_sha256': digest(truth), 'generating_witness_verified': True,
                                      'recovery_status': 'NOT_RUN', 'statistics': statistics(public.ciphertext),
                                      'matching': 'Same dictionary/model and word count; NOT ciphertext lengths. Exact length matching impossible at target word 23.'})
    report['complete'] = True
    write_json(OUTPUT, report)
    print(json.dumps(report['boundary'], indent=2))
    print(f'Prepared {len(report["experiments"])} prefixes and {len(report["controls"])} controls; no solver calls. Saved {OUTPUT}')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms', type=int, default=1800000)
    args = parser.parse_args()
    run(args.timeout_ms)
