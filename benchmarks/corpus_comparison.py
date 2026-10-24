"""Small bounded real-text pilot with matched controls and a synthetic gate."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform

import z3

from voynich_smt.cipher.base import Bounds, generate_encoder, generate_ciphertext
from voynich_smt.data.controls import control
from voynich_smt.data.corpus import Corpus, statistics, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text


def run(voynich, latin, output, words=5, seed=7, timeout_ms=10000, vocabulary_size=32,
        artifact_dir=Path('data/generated/corpus-pilot')):
    observed, selection = voynich.sample(words, folio='f1r')
    candidates = []
    for r in latin.records:
        word = tuple(r['tokens'])
        if word and word not in candidates and len(word) <= 12:
            candidates.append(word)
        if len(candidates) == vocabulary_size:
            break
    if len(candidates) != vocabulary_size:
        raise ValueError('Insufficient Latin vocabulary')
    dictionary = WordDictionary(tuple(candidates))
    plain = Alphabet(tuple(latin.normalization['alphabet']))
    # Use all eligible EVA units, ensuring the same public cipher alphabet in every run.
    cipher = Alphabet(tuple(sorted({g for r in voynich.records for g in r['tokens']})))
    bounds = Bounds('verbose', 1, 1, 2)
    latin_selection = [(i, tuple(r['tokens'])) for i, r in enumerate(latin.records)
                       if tuple(r['tokens']) in candidates][:words]
    if len(latin_selection) != words:
        raise ValueError('Insufficient Latin words under the public dictionary')
    plaintext = Text(tuple(word for _, word in latin_selection))
    encoder = generate_encoder(plain, cipher, bounds, seed)
    encrypted, choices = generate_ciphertext(plaintext, encoder, seed + 1)
    root = artifact_dir / 'inputs'
    report = {'schema_version': 1, 'complete': False, 'environment': {'python': platform.python_version(),
              'z3': z3.get_version_string(), 'platform': platform.platform()},
              'selection': selection, 'latin_source': latin.source, 'latin_corpus_sha256': latin.identity,
              'language_model': {'kind': 'finite corpus-derived dictionary', 'words': candidates,
                                  'selection': 'first distinct eligible Latin words of length <=12',
                                  'vocabulary_size': vocabulary_size},
              'comparison_matching': 'word count; randomized/pseudo controls also match EVA word lengths',
              'synthetic_matching': 'same cipher bounds, alphabets, dictionary and word count; token lengths differ',
              'experiments': [], 'synthetic_gate_passed': False,
              'interpretation': 'Bounded pilot only; corpus-derived dictionary is not unrestricted Latin.'}
    write_json(artifact_dir / 'ground_truth.json',
               {'plaintext': asdict(plaintext), 'encoder': asdict(encoder), 'choices': choices, 'seed': seed})
    inputs = [('synthetic-latin-cipher', encrypted,
               {'seed': seed, 'latin_corpus_sha256': latin.identity,
                'record_indices': [i for i, _ in latin_selection],
                'selection': 'first corpus words admitted by the public dictionary'}), ('voynich', observed, selection)]
    inputs += [(kind, *control(observed, kind, seed)) for kind in
               ('word-shuffle', 'within-word-shuffle', 'frequency-shuffle', 'uniform', 'prefix-stem-suffix')]
    for kind, ciphertext, metadata in inputs:
        request = HiddenRecoveryRequest(ciphertext=ciphertext, plaintext_alphabet=plain,
                   ciphertext_alphabet=cipher, bounds=bounds, dictionary=dictionary,
                   timeout_ms=timeout_ms, representation='finite')
        public_path = root / f'{kind}.json'
        write_json(public_path, asdict(request))
        request = HiddenRecoveryRequest.from_dict(json.loads(public_path.read_text()))
        result = request.solve()
        if kind == 'synthetic-latin-cipher':
            report['synthetic_gate_passed'] = result.status == 'SAT' and result.verified
        report['experiments'].append({'dataset': kind, 'sample_metadata': metadata, 'public_input': str(public_path),
                                      'request': asdict(request), 'statistics': statistics(ciphertext),
                                      'result': asdict(result)})
        write_json(output, report)
        print(f'{kind}: {result.status}, {result.runtime_seconds:.3f}s, verified={result.verified}', flush=True)
    report['latin_statistics'] = statistics(Text(tuple(tuple(r['tokens']) for r in latin.records if r['tokens'])))
    report['voynich_statistics'] = statistics(Text(tuple(tuple(r['tokens']) for r in voynich.records if r['tokens'])))
    report['complete'] = True
    write_json(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--voynich', type=Path, default=Path('data/processed/zl-eva.json'))
    parser.add_argument('--latin', type=Path, default=Path('data/processed/caesar-latin.json'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/corpus-pilot.json'))
    parser.add_argument('--words', type=int, default=5)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--timeout-ms', type=int, default=10000)
    parser.add_argument('--vocabulary-size', type=int, default=32)
    parser.add_argument('--artifact-dir', type=Path, default=Path('data/generated/corpus-pilot'))
    args = parser.parse_args()
    if args.words <= 0 or args.timeout_ms <= 0 or args.vocabulary_size <= 0:
        parser.error('Words, timeout, and vocabulary size must be positive')
    run(Corpus.load(args.voynich), Corpus.load(args.latin), args.output,
        args.words, args.seed, args.timeout_ms, args.vocabulary_size, args.artifact_dir)


if __name__ == '__main__':
    main()
