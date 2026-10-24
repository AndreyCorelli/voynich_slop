"""Work-disjoint natural English development pilot; not published reproduction."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import random
import time

from voynich_smt.word_mapping.ravi_knight.english import PARSER_VERSION, extract, prefix_segments, source_loss
from voynich_smt.word_mapping.ravi_knight.iterative import fit_iterative
from voynich_smt.word_mapping.ravi_knight.lm import train_bigram


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(raw_dir, output, *, sizes=(10, 20, 30), iterations=200, tokens=500, budget=3600.,
        initialization='random', freeze=True, frequency_strength=0.5,
        warm_start=False, exploration=0.05, smoothing=0.1, reference_run=None):
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError('budget must be positive')
    started = time.monotonic()
    if (output / 'protocol.json').exists():
        raise FileExistsError('Use a fresh output directory to preserve prior runs')
    output.mkdir(parents=True, exist_ok=True)
    raw = {book: (raw_dir / f'{book}.txt').read_bytes() for book in ('1342', '11')}
    training = extract(raw['1342'].decode('utf-8-sig'), '1342')
    truth = prefix_segments(extract(raw['11'].decode('utf-8-sig'), '11'), tokens)
    # Selection/configuration is frozen before recovery metrics are computed.
    protocol = {'parser': PARSER_VERSION, 'raw_sha256': {k: sha(v) for k, v in raw.items()},
                'training_work': '1342', 'evaluation_work': '11', 'sizes': sizes,
                'max_iterations': iterations, 'requested_tokens': tokens, 'search_seeds': [3, 5, 7],
                'warm_start': warm_start, 'exploration': exploration,
                'initialization': initialization, 'freeze': freeze, 'frequency_strength': frequency_strength,
                'smoothing': smoothing, 'channel_exponent': 3, 'budget_seconds': budget,
                'budget_policy': 'cooperative between chains; one chain can exceed remaining budget',
                'selection': 'first complete segments fitting token limit; no coverage filtering'}
    if reference_run is not None:
        protocol['reference_run'] = str(reference_run)
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    words = sorted({w for s in truth for w in s})
    random.Random(71).shuffle(words)
    key = {w: f'c{i:05}' for i, w in enumerate(words)}
    cipher_order = None
    reference_truth = None
    if reference_run is not None:
        reference_public = json.loads((reference_run / 'public.json').read_text())
        reference_truth = json.loads((reference_run / 'evaluation-only' / 'truth.json').read_text())
        if [list(s) for s in truth[:len(reference_truth['plaintext'])]] != reference_truth['plaintext']:
            raise ValueError('Reference plaintext is not a nested prefix')
        # Fixture preparation only: preserve prior identities and assign new opaque IDs.
        key = dict(reference_truth['key'])
        for w in words:
            if w not in key:
                key[w] = f'c{len(key):05}'
        reference_counts = Counter(c for s in reference_public['ciphertext'] for c in s)
        cipher_order = sorted(reference_counts, key=lambda c: (-reference_counts[c], c))
    cipher = tuple(tuple(key[w] for w in s) for s in truth)
    # Truth is stored separately; neither key nor seed goes in inference input.
    (output / 'evaluation-only').mkdir(exist_ok=True)
    (output / 'evaluation-only' / 'truth.json').write_text(json.dumps({'plaintext': truth, 'key': key}))
    public = {'training': training, 'ciphertext': cipher}
    if cipher_order is not None:
        public['cipher_order'] = cipher_order
    (output / 'public.json').write_text(json.dumps(public))
    source = train_bigram(training, max_types=sizes[-1], smoothing=smoothing)
    counts = Counter(c for s in cipher for c in s)
    ranks = cipher_order or sorted(counts, key=lambda c: (-counts[c], c))
    frequency = {c: source.vocabulary[i + 1] if i + 1 < len(source.vocabulary) else '<UNKNOWN>'
                 for i, c in enumerate(ranks)}
    total = sum(map(len, truth))
    prefix_count = len(reference_truth['plaintext']) if reference_truth else len(truth)
    prefix_tokens = sum(map(len, truth[:prefix_count]))
    def metrics(decoded):
        correct = sum(a == b for s, t in zip(decoded, truth) for a, b in zip(s, t))
        owners = {}
        for s, t in zip(cipher, decoded):
            for c, w in zip(s, t):
                owners.setdefault(c, set()).add(w)
        prefix_correct = sum(a == b for s, t in zip(decoded[:prefix_count], truth[:prefix_count]) for a, b in zip(s, t))
        return {'token_accuracy': correct / total, 'prefix_token_accuracy': prefix_correct / prefix_tokens,
                'inconsistent_cipher_types': sum(len(v) > 1 for v in owners.values())}
    evaluation_segments = extract(raw['11'].decode('utf-8-sig'), '11')
    excluded = prefix_segments(evaluation_segments, 2000)
    lm_development = prefix_segments(evaluation_segments[len(excluded):], 2000)
    result = {'lm_development': source_loss(source, lm_development), 'protocol': protocol, 'public_sha256': sha(json.dumps(public, sort_keys=True).encode()),
              'scope': 'work-disjoint development pilot, not published reproduction',
              'training_tokens': sum(map(len, training)), 'cipher_tokens': total,
              'cipher_types': len(words), 'prefix_tokens': prefix_tokens, 'frequency': metrics(tuple(tuple(frequency.get(c, '<UNKNOWN>') for c in s) for s in cipher)),
              'runs': [], 'skipped_seeds': []}
    for seed in protocol['search_seeds']:
        if time.monotonic() - started >= budget:
            result['skipped_seeds'].append(seed)
            continue
        stages = fit_iterative(training, cipher, sizes=sizes, seed=seed, max_iterations=iterations,
                               initialization=initialization, freeze=freeze, frequency_strength=frequency_strength,
                               warm_start=warm_start, exploration=exploration, smoothing=smoothing, cipher_order=cipher_order)
        reports = []
        for stage in stages:
            decoded = stage.decode(cipher)
            vocab = set(stage.source.vocabulary[1:])
            reports.append({'types': stage.requested_types, 'source': asdict(stage.source),
                            'cipher_vocabulary': stage.cipher_vocabulary, 'channel': stage.result.model.channel,
                            'frozen': stage.frozen, 'log_likelihoods': stage.result.log_likelihoods,
                            'converged': stage.result.converged, 'cipher_coverage': stage.cipher_coverage,
                            'candidate_token_ceiling': sum(w in vocab for s in truth for w in s) / total,
                            'decoded': decoded, **metrics(decoded)})
        result['runs'].append({'seed': seed, 'stages': reports})
        result['elapsed_seconds'] = time.monotonic() - started
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    result['elapsed_seconds'] = time.monotonic() - started
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=Path('data/raw/ravi-knight-english'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/ravi-knight/natural-english-v1'))
    parser.add_argument('--sizes', type=int, nargs='+', default=[10, 20, 30])
    parser.add_argument('--iterations', type=int, default=200,
                        help='Per-stage cap; pilot default 200, override for scale studies')
    parser.add_argument('--initialization', choices=['random', 'frequency'], default='random')
    parser.add_argument('--warm-start', action='store_true', help='Transfer revisable rows; implies no freezing')
    parser.add_argument('--exploration', type=float, default=0.05)
    parser.add_argument('--no-freeze', action='store_true')
    parser.add_argument('--frequency-strength', type=float, default=0.5)
    parser.add_argument('--smoothing', type=float, default=0.1)
    parser.add_argument('--reference-run', type=Path, help='Preserve cipher identities/ranks and evaluate original prefix')
    parser.add_argument('--tokens', type=int, default=500)
    parser.add_argument('--budget-seconds', type=float, default=3600.)
    args = parser.parse_args()
    result = run(args.raw_dir, args.output, sizes=tuple(args.sizes), iterations=args.iterations,
                 tokens=args.tokens, budget=args.budget_seconds, initialization=args.initialization,
                 freeze=not (args.no_freeze or args.warm_start), frequency_strength=args.frequency_strength,
                 warm_start=args.warm_start, exploration=args.exploration, smoothing=args.smoothing,
                 reference_run=args.reference_run)
    print(json.dumps({'frequency': result['frequency'], 'seconds': result['elapsed_seconds'],
                      'runs': [{'seed': r['seed'], 'final': {k: r['stages'][-1][k] for k in
                               ('token_accuracy', 'candidate_token_ceiling', 'inconsistent_cipher_types')}}
                               for r in result['runs']]}))


if __name__ == '__main__':
    main()
