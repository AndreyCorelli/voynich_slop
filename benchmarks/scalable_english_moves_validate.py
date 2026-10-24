"""Replay engineering move choices independently and fully rescore the final key."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram


def validate(resources, output):
    report = json.loads((output / 'report.json').read_text())
    stream = CipherStream.load(output / 'public/cipher.json')
    inventory = Inventory(resources / 'inventory.sqlite')
    try:
        model = SparseBigram.load(resources / 'model.sqlite', inventory)
        assert stream.identity == report['cipher_sha256']
        assert model.identity == report['model_sha256']
        assignments = random.Random(19).sample(range(model.size), stream.type_count)
        owner = {w: c for c, w in enumerate(assignments)}
        score = lambda: sum(model.score(assignments[c] for c in doc) for doc in stream.documents)
        assert abs(score() - report['initial_score']) < 1e-8
        rng, accepted, swaps, replacements, noops = random.Random(23), 0, 0, 0, 0
        for _ in range(report['requested_proposals']):
            cipher, word = rng.randrange(stream.type_count), rng.randrange(model.size)
            other = owner.get(word)
            if other == cipher:
                noops += 1
            elif other is None:
                replacements += 1
            else:
                swaps += 1
            if rng.random() < .5:
                old = assignments[cipher]
                if other is None:
                    del owner[old]
                else:
                    assignments[other] = old
                    owner[old] = other
                assignments[cipher] = word
                owner[word] = cipher
                accepted += 1
        assert assignments == report['final_assignments']
        assert len(owner) == len(assignments) == len(set(assignments))
        assert abs(score() - report['final_score']) < 1e-8
        assert (accepted, swaps, replacements, noops) == tuple(report[k] for k in ('accepted', 'swaps', 'replacements', 'noops'))
        counts = Counter()
        for doc in stream.documents:
            counts.update(zip((-1,) + doc, doc + (-2,)))
        assert len(counts) == report['aggregated_events']
        assert sum(counts.values()) == report['scoring_event_occurrences']
        return {'status': 'validated', 'tokens': sum(map(len, stream.documents)),
                'cipher_types': len(assignments), 'replayed_proposals': report['requested_proposals']}
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/scalable-english/dictionary-moves-ewt-v2'))
    args = parser.parse_args()
    print(json.dumps(validate(args.resources, args.output), indent=2))
