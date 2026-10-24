"""Small generated-English EM diagnostic, not a published benchmark reproduction."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import time

from voynich_smt.word_mapping.ravi_knight.em import fit_channel, random_channel
from voynich_smt.word_mapping.ravi_knight.lm import train_bigram
from voynich_smt.word_mapping.ravi_knight.reference import viterbi


def sentences(seed, size):
    rng = random.Random(seed)
    return tuple((rng.choice(('the', 'the', 'a')), rng.choice(('cat', 'dog')),
                  rng.choice(('sees', 'follows')), 'the', rng.choice(('cat', 'dog')))
                 for _ in range(size))


def run(*, max_iterations=60):
    started = time.perf_counter()
    training = sentences(11, 300)
    plaintext = sentences(29, 60)
    source = train_bigram(training)
    # Only training defines source vocabulary. Truth/key remain local to this
    # benchmark's fixture/evaluation layer and are never passed to fit_channel.
    words = sorted({w for s in plaintext for w in s})
    shuffled = words.copy()
    random.Random(71).shuffle(shuffled)
    encryption = {w: i for i, w in enumerate(shuffled)}
    cipher = tuple(tuple(encryption[w] for w in s) for s in plaintext)
    cipher_counts = Counter(c for s in cipher for c in s)
    source_ranks = sorted(range(1, len(source.vocabulary)),
                          key=lambda s: (-source.counts[s], source.vocabulary[s]))
    cipher_ranks = sorted(cipher_counts, key=lambda c: (-cipher_counts[c], c))
    frequency = dict(zip(cipher_ranks, source_ranks))
    truth_ids = source.encode(plaintext)
    def accuracy(decoded):
        return sum(a == b for s, t in zip(decoded, truth_ids) for a, b in zip(s, t)) / sum(map(len, cipher))
    results = []
    for seed in (3, 5, 7):
        initial = source.hmm(random_channel(len(source.vocabulary), len(words), seed=seed))
        fitted = fit_channel(initial, cipher, max_iterations=max_iterations)
        decoded = tuple(viterbi(fitted.model, s, channel_exponent=3)[0] for s in cipher)
        results.append({'seed': seed, 'updates': len(fitted.log_likelihoods) - 1,
                        'converged': fitted.converged,
                        'log_likelihoods': fitted.log_likelihoods,
                        'token_accuracy': accuracy(decoded),
                        'channel': fitted.model.channel, 'decoded': decoded})
    # Hash the exact public numerical input; exclude fixture plaintext and key.
    public = {'source': asdict(source), 'cipher': cipher}
    identity = hashlib.sha256(json.dumps(public, sort_keys=True).encode()).hexdigest()
    return {'format_version': 1, 'scope': 'generated-English fixed-vocabulary development diagnostic',
            'not_published_reproduction': True, 'public_input_sha256': identity,
            'public_input': public, 'training_seed': 11, 'evaluation_seed': 29,
            'training_sentences': len(training), 'cipher_sentences': len(cipher),
            'cipher_tokens': sum(map(len, cipher)), 'source_types_including_unknown': len(source.vocabulary),
            'cipher_types': len(words), 'max_iterations': max_iterations,
            'frequency_token_accuracy': accuracy(tuple(tuple(frequency[c] for c in s) for s in cipher)),
            'runs': results, 'elapsed_seconds': time.perf_counter() - started,
            'limitations': ['Tiny shared synthetic sentence family; not natural prose.',
                            'Independent sampling can repeat identical sentences.',
                            'Training and decipherment share a domain.',
                            'Accuracy is measured on the ciphertext used for unsupervised fitting.',
                            'Token Viterbi output need not form a consistent dictionary.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-iterations', type=int, default=60)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run(max_iterations=args.max_iterations)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('frequency_token_accuracy', 'elapsed_seconds')}))
    print(json.dumps([{'seed': r['seed'], 'token_accuracy': r['token_accuracy'],
                       'updates': r['updates']} for r in result['runs']]))


if __name__ == '__main__':
    main()
