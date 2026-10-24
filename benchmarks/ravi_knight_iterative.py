"""Paired freezing diagnostic on the existing generated-English fixture."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random
import time

from benchmarks.ravi_knight_em import sentences
from voynich_smt.word_mapping.ravi_knight.iterative import fit_iterative


def run(*, max_iterations=60):
    started = time.perf_counter()
    training, truth = sentences(11, 300), sentences(29, 60)
    words = sorted({w for s in truth for w in s})
    random.Random(71).shuffle(words)
    key = {word: f'c{i}' for i, word in enumerate(words)}
    cipher = tuple(tuple(key[w] for w in s) for s in truth)
    runs = []
    for freeze in (True, False):
        for seed in (3, 5, 7):
            stages = fit_iterative(training, cipher, sizes=(2, 4, 6), seed=seed,
                                   freeze=freeze, max_iterations=max_iterations)
            reports = []
            for stage in stages:
                decoded = stage.decode(cipher)
                correct = sum(a == b for s, t in zip(decoded, truth) for a, b in zip(s, t))
                reports.append({'requested_types': stage.requested_types,
                                'source': asdict(stage.source),
                                'cipher_vocabulary': stage.cipher_vocabulary,
                                'frozen': stage.frozen,
                                'source_coverage': stage.source_coverage,
                                'cipher_coverage': stage.cipher_coverage,
                                'log_likelihoods': stage.result.log_likelihoods,
                                'channel': stage.result.model.channel,
                                'converged': stage.result.converged,
                                'decoded': decoded,
                                'token_accuracy': correct / sum(map(len, truth))})
            runs.append({'seed': seed, 'freeze': freeze, 'stages': reports})
    return {'format_version': 1, 'scope': 'generated-English iterative EM development diagnostic',
            'not_published_reproduction': True, 'max_iterations_per_stage': max_iterations,
            'sizes': [2, 4, 6], 'ciphertext': cipher, 'runs': runs,
            'elapsed_seconds': time.perf_counter() - started,
            'limitations': ['Reused development fixture; not independent validation.',
                            'Small synthetic sentence family, not natural English.',
                            'No-freeze condition reinitializes rather than warm-starting.',
                            'UNKNOWN pairs do not freeze; additive-smoothed source LM.',
                            'Likelihoods must not be compared across vocabulary stages.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-iterations', type=int, default=60)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run(max_iterations=args.max_iterations)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'elapsed_seconds': result['elapsed_seconds'], 'runs': [
        {'seed': r['seed'], 'freeze': r['freeze'],
         'accuracy_by_stage': [s['token_accuracy'] for s in r['stages']],
         'frozen_by_stage': [len(s['frozen']) for s in r['stages']]} for r in result['runs']]}))


if __name__ == '__main__':
    main()
