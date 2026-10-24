"""Validate sparse-foundation artifacts and recompute development diagnostics."""
from array import array
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import random

from benchmarks.scalable_english_build import documents
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import BOS, SparseBigram


def validate(raw_dir, output):
    report = json.loads((output / 'report.json').read_text())
    for name, expected in report['sources'].items():
        if hashlib.sha256((raw_dir / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Raw source identity mismatch')
    inventory = Inventory(output / 'inventory.sqlite')
    try:
        model = SparseBigram.load(output / 'model.sqlite', inventory)
        assert inventory.identity == report['inventory_sha256']
        assert model.identity == report['model_sha256']
        counts, edges = array('Q', [0]) * (inventory.size + 1), Counter()
        for doc in documents(raw_dir / 'en_ewt-r2.17-train.conllu'):
            ids = [inventory.id(w) for w in doc.words]
            for w in ids:
                counts[w] += 1
            counts[-1] += 1
            edges.update(zip([BOS] + ids, ids + [inventory.size]))
        assert counts == model.counts and dict(edges) == model.edges
        assert sum(model.base_probability(w) for w in range(inventory.size + 1)) == 1. or abs(
            sum(model.base_probability(w) for w in range(inventory.size + 1)) - 1) < 1e-10
        # Sum discounted seen terms plus the normalized backoff term per row.
        seen_mass = Counter()
        for (a, _), n in edges.items():
            seen_mass[a] += n - model.config.discount
        for a, mass in seen_mass.items():
            assert abs(mass / model.totals[a] + model.config.discount * model.distinct[a] / model.totals[a] - 1) < 1e-12
        rng = random.Random(17)
        docs, tokens, missing, covered, scored, events = 0, 0, 0, 0, 0, 0
        genuine, shuffled = 0., 0.
        for doc in documents(raw_dir / 'en_ewt-r2.17-dev.conllu'):
            docs += 1
            tokens += len(doc.words)
            ids, absent = [], 0
            for w in doc.words:
                try:
                    ids.append(inventory.id(w))
                except KeyError:
                    absent += 1
            missing += absent
            if absent:
                continue
            covered += 1
            scored += len(ids)
            events += len(ids) + 1
            genuine += model.score(ids)
            rng.shuffle(ids)
            shuffled += model.score(ids)
        expected = report['development']
        assert (docs, tokens, missing, covered, scored) == tuple(expected[k] for k in (
            'documents', 'tokens', 'missing_tokens', 'fully_covered_documents', 'scored_tokens'))
        if events:
            assert abs(-genuine/events - expected['genuine_nats_per_event']) < 1e-12
            assert abs(-shuffled/events - expected['shuffled_nats_per_event']) < 1e-12
        return {'inventory_forms': inventory.size, 'observed_edges': len(edges),
                'covered_development_documents': covered, 'status': 'validated'}
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=Path('data/raw/scalable-english'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    args = parser.parse_args()
    print(json.dumps(validate(args.raw_dir, args.output), indent=2))
