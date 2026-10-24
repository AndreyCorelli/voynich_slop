"""Replay candidate retrieval and independently rescore selected candidate moves."""
import argparse
import math
from collections import Counter
import json
from pathlib import Path

from benchmarks.scalable_english_retrieval import infer
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.retrieval import ContextIndex, RetrievalConfig
from voynich_smt.word_mapping.scalable.sparse_lm import BOS, SparseBigram


def validate(resources, output):
    report = json.loads((output / 'report.json').read_text())
    protocol = json.loads((output / 'protocol.json').read_text())
    stream = CipherStream.load(output / 'public/cipher.json')
    inventory = Inventory(resources / 'inventory.sqlite')
    try:
        model = SparseBigram.load(resources / 'model.sqlite', inventory)
        assert stream.identity == protocol['cipher_sha256']
        assert model.identity == protocol['model_sha256']
        config = RetrievalConfig(**protocol['config'])
        replay = infer(model, stream, protocol['selected_types'], config)
        for key in ('rows', 'offered_pools', 'proposals', 'initial_assignments', 'active_entries', 'archive_entries',
                    'cached_context_queries', 'cache_hits', 'cache_misses'):
            assert json.loads(json.dumps(replay[key])) == report[key]
        assert report['active_entries'] <= config.total_entries
        assert report['archive_entries'] <= config.total_entries
        initial = report['initial_assignments']
        owners = {w: c for c, w in enumerate(initial)}
        def score(key):
            return sum(model.score(key[c] for c in d) for d in stream.documents)
        before = score(initial)
        checked = 0
        for row in report['rows']:
            assert len(row['candidates']) <= config.active_limit
            assert row['pool_size'] <= config.pool_limit
            assert initial[row['cipher']] in {c['word_id'] for c in row['candidates']}
            # Best and last candidate: full direct scoring, not local deltas.
            positions = sorted({0, len(row['candidates']) - 1})
            for pos in positions:
                candidate = row['candidates'][pos]
                key = list(initial)
                other = owners.get(candidate['word_id'])
                if other is not None:
                    key[other] = initial[row['cipher']]
                key[row['cipher']] = candidate['word_id']
                assert len(set(key)) == stream.type_count
                assert abs(score(key) - before - candidate['log_delta']) < 1e-7
                checked += 1
        truth = json.loads((output / 'evaluation-only/truth.json').read_text())
        assert truth['public_sha256'] == stream.identity
        true_ids = [inventory.id(w) for w in truth['decoding']]
        hits = sum(true_ids[row['cipher']] in {c['word_id'] for c in row['candidates']} for row in report['rows'])
        assert hits / len(report['rows']) == report['active_type_recall']
        offered_hits = sum(true_ids[row['cipher']] in pool for row, pool in zip(report['rows'], report['offered_pools']))
        assert offered_hits / len(report['rows']) == report['offered_pool_type_recall']
        counts = Counter(c for d in stream.documents for c in d)
        weighted = sum(counts[row['cipher']] for row in report['rows']
                       if true_ids[row['cipher']] in {c['word_id'] for c in row['candidates']})
        assert weighted / sum(counts[row['cipher']] for row in report['rows']) == report['active_token_weighted_recall_on_sample']
        context = ContextIndex(model, limit=config.per_context, cache_queries=config.cache_queries)
        positions = [[] for _ in range(stream.type_count)]
        for doc_id, doc in enumerate(stream.documents):
            for pos, cipher in enumerate(doc):
                positions[cipher].append((doc_id, pos))
        oracle_hits = 0
        for row in report['rows']:
            cipher = row['cipher']
            occurrences = positions[cipher]
            offered = set()
            samples = min(len(occurrences), config.context_limit)
            for i in range(samples):
                doc_id, pos = occurrences[i * len(occurrences) // samples]
                doc = stream.documents[doc_id]
                left = BOS if pos == 0 else true_ids[doc[pos - 1]]
                right = model.eos if pos + 1 == len(doc) else true_ids[doc[pos + 1]]
                offered.update(context.query('successors', left))
                offered.update(context.query('predecessors', right))
            oracle_hits += true_ids[cipher] in offered
        assert oracle_hits / len(report['rows']) == report['oracle_neighbor_context_recall_diagnostic']
        return {'status': 'validated' , 'candidate_rows_replayed': len(report['rows']),
                'proposals_replayed': len(report['proposals']), 'full_candidate_score_checks': checked}
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/scalable-english/retrieval-ewt-v2'))
    args = parser.parse_args()
    print(json.dumps(validate(args.resources, args.output), indent=2))
