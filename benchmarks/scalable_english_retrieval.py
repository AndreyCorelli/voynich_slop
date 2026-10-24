"""Candidate-support engineering diagnostic, not decipherment or final evaluation."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import random
import resource
import sys
import time

from benchmarks.scalable_english_build import documents
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.retrieval import CandidateRetriever, RetrievalConfig
from voynich_smt.word_mapping.scalable.sparse_lm import BOS, SparseBigram
from voynich_smt.word_mapping.scalable.state import DictionaryState


def infer(model, stream, selected, config):
    """No raw prose, original word IDs, key or evaluation truth is accepted."""
    state = DictionaryState.random(stream, model, seed=19)
    scorer = DictionaryScorer(model, stream, state)
    started = time.perf_counter()
    retriever = CandidateRetriever(scorer, config=config, seed=29)
    index_seconds = time.perf_counter() - started
    rows, exploration, offered = [], [], []
    start = time.perf_counter()
    for cipher in selected:
        row = retriever.refresh(cipher, audit=lambda candidates: offered.append([c.word_id for c in candidates]))
        rows.append(asdict(row))
    refresh_seconds = time.perf_counter() - start
    # Reject proposals: exercise both sources without turning this into a search.
    for _ in range(1000):
        cipher = selected[retriever.rng.randrange(len(selected))]
        move, source = retriever.propose(cipher)
        target = dict(move.changes).get(cipher, scorer.assignment(cipher))
        exploration.append({'cipher': cipher, 'word_id': target, 'source': source})
    scorer.validate()
    return {'rows': rows, 'offered_pools': offered, 'proposals': exploration, 'index_seconds': index_seconds,
            'refresh_seconds': refresh_seconds, 'active_entries': retriever.entry_count,
            'archive_entries': retriever.archive_entry_count,
            'cached_context_queries': len(retriever.contexts._cache),
            'cache_hits': retriever.contexts.cache_hits, 'cache_misses': retriever.contexts.cache_misses,
            'initial_assignments': state.assignments}


def run(resources, raw, output, *, tokens=35000, sampled_types=64):
    if type(sampled_types) is not int or sampled_types < 1:
        raise ValueError('sampled_types must be positive')
    output.mkdir(parents=True, exist_ok=False)
    inventory = Inventory(resources / 'inventory.sqlite')
    try:
        model = SparseBigram.load(resources / 'model.sqlite', inventory)
        remaining, plaintext = tokens, []
        for doc in documents(raw):
            plaintext.append(doc.words[:remaining])
            remaining -= len(plaintext[-1])
            if not remaining:
                break
        if remaining:
            raise ValueError('Insufficient corpus tokens')
        stream, truth = generate(plaintext, seed=83)
        stream.save(output / 'public/cipher.json')
        truth.save(output / 'evaluation-only/truth.json')
        # Public-only selection: include frequent and seeded uniformly sampled types.
        frequencies = Counter(c for d in stream.documents for c in d)
        counts = [frequencies[c] for c in range(stream.type_count)]
        count = min(sampled_types, stream.type_count)
        frequent = sorted(range(stream.type_count), key=lambda c: (-counts[c], c))[:min(8, count)]
        selected = frequent + random.Random(37).sample([c for c in range(stream.type_count) if c not in frequent], count - len(frequent))
        config = RetrievalConfig(total_entries=max(100, count * 100))
        (output / 'protocol.json').write_text(json.dumps({'config': asdict(config), 'selected_types': selected,
            'initialization_seed': 19, 'retrieval_seed': 29, 'selection_seed': 37,
            'cipher_sha256': stream.identity, 'model_sha256': model.identity}, indent=2) + '\n')
        started = time.perf_counter()
        inference = infer(model, stream, selected, config)
        # Only now inspect hidden truth. Never pass these IDs to infer/refresh.
        true_ids = tuple(inventory.id(w) for w in truth.decoding)
        active_hits = sum(true_ids[row['cipher']] in {c['word_id'] for c in row['candidates']} for row in inference['rows'])
        offered_hits = sum(true_ids[row['cipher']] in pool for row, pool in zip(inference['rows'], inference['offered_pools']))
        exploration_pool_hits = sum(true_ids[row['cipher']] in row['proposed_exploration'] for row in inference['rows'])
        weighted_hits = sum(counts[row['cipher']] for row in inference['rows']
                            if true_ids[row['cipher']] in {c['word_id'] for c in row['candidates']})
        # Explicitly assisted diagnostic: neighbor-only retrieval under true
        # contexts. Do not include protected current assignments as candidates.
        from voynich_smt.word_mapping.scalable.retrieval import ContextIndex
        contexts = ContextIndex(model, limit=config.per_context, cache_queries=config.cache_queries)
        positions = [[] for _ in range(stream.type_count)]
        for doc_id, doc in enumerate(stream.documents):
            for position, c in enumerate(doc):
                positions[c].append((doc_id, position))
        oracle_hits = 0
        for cipher in selected:
            candidates = set()
            occurrence = positions[cipher]
            for i in range(min(len(occurrence), config.context_limit)):
                doc_id, pos = occurrence[i * len(occurrence) // min(len(occurrence), config.context_limit)]
                doc = stream.documents[doc_id]
                left = BOS if pos == 0 else true_ids[doc[pos - 1]]
                right = model.eos if pos + 1 == len(doc) else true_ids[doc[pos + 1]]
                candidates.update(contexts.query('successors', left))
                candidates.update(contexts.query('predecessors', right))
            oracle_hits += true_ids[cipher] in candidates
        report = {'scope': 'cold-state candidate support; no optimization or recovery claim',
            'tokens': tokens, 'documents': len(stream.documents), 'cipher_types': stream.type_count,
            'inventory_forms': inventory.size, 'sampled_types': count, 'frequent_types_in_sample': len(frequent),
            'offered_pool_type_recall': offered_hits / count,
            'active_type_recall': active_hits / count,
            'active_token_weighted_recall_on_sample': weighted_hits / sum(counts[c] for c in selected),
            'random_refresh_pool_hits': exploration_pool_hits,
            'oracle_neighbor_context_recall_diagnostic': oracle_hits / count,
            'elapsed_seconds': time.perf_counter() - started, **inference,
            'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
            'limitations': ['Sample includes frequent types and is not representative of all cipher types.',
                'Fixture also occurs in LM training; oracle-context diagnostic is optimistic.',
                'Combined shortlist is heuristic; only individual context indexes are exact.',
                'No proposals are accepted and no decipherment result is reported.',
                'Inventory is 15k forms; million-form scale remains unmeasured.']}
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        return report
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--raw', type=Path, default=Path('data/raw/scalable-english/en_ewt-r2.17-train.conllu'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/scalable-english/retrieval-ewt-v2'))
    parser.add_argument('--tokens', type=int, default=35000)
    parser.add_argument('--sampled-types', type=int, default=64)
    args = parser.parse_args()
    result = run(args.resources, args.raw, args.output, tokens=args.tokens, sampled_types=args.sampled_types)
    print(json.dumps({k:v for k,v in result.items() if k not in {'rows', 'offered_pools', 'proposals', 'initial_assignments'}}, indent=2))
