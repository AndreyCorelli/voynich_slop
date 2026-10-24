"""Independently recompute saved natural-English metrics and model evidence."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from voynich_smt.word_mapping.ravi_knight.em import expectation
from voynich_smt.word_mapping.ravi_knight.reference import BigramHMM, viterbi


def validate(root):
    result = json.loads((root / 'result.json').read_text())
    public = json.loads((root / 'public.json').read_text())
    truth = json.loads((root / 'evaluation-only' / 'truth.json').read_text())['plaintext']
    total = sum(map(len, truth))
    checked = 0
    for run in result['runs']:
        for stage in run['stages']:
            source = stage['source']
            model = BigramHMM(source['initial'], source['transition'], source['final'], stage['channel'])
            ids = {w: i for i, w in enumerate(stage['cipher_vocabulary'])}
            obs = tuple(tuple(ids.get(w, 0) for w in s) for s in public['ciphertext'])
            decoded = [[source['vocabulary'][i] for i in viterbi(model, s, channel_exponent=3)[0]] for s in obs]
            assert decoded == stage['decoded']
            assert abs(expectation(model, obs)[0] - stage['log_likelihoods'][-1]) < 1e-7
            accuracy = sum(a == b for s, t in zip(decoded, truth) for a, b in zip(s, t)) / total
            assert abs(accuracy - stage['token_accuracy']) < 1e-12
            if 'prefix_token_accuracy' in stage:
                pairs = [(a, b) for s, t in zip(decoded, truth) for a, b in zip(s, t)]
                prefix = pairs[:result['prefix_tokens']]
                assert abs(sum(a == b for a, b in prefix) / len(prefix) - stage['prefix_token_accuracy']) < 1e-12
            owners = defaultdict(set)
            for segment, decoded_segment in zip(public['ciphertext'], decoded):
                for c, w in zip(segment, decoded_segment):
                    owners[c].add(w)
            assert sum(len(v) > 1 for v in owners.values()) == stage['inconsistent_cipher_types']
            vocab = set(source['vocabulary'][1:])
            ceiling = sum(w in vocab for s in truth for w in s) / total
            assert abs(ceiling - stage['candidate_token_ceiling']) < 1e-12
            for word, cipher in stage['frozen']:
                assert model.channel[source['vocabulary'].index(word)][ids[cipher]] == 1
            assert all(b >= a - 1e-7 for a, b in zip(stage['log_likelihoods'], stage['log_likelihoods'][1:]))
            checked += 1
    return checked


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(f'Validated {validate(args.root)} saved stages')
