"""Build/profile sparse foundations on pinned modern EWT engineering data.

This does not run decipherment or certify the final independent benchmark.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import random
import resource
import sys
import time

from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.corpora import read_ewt
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram


def documents(path):
    with path.open(encoding='utf-8') as stream:
        yield from read_ewt(stream)


def build(raw_dir, output):
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    train = raw_dir / 'en_ewt-r2.17-train.conllu'
    dev = raw_dir / 'en_ewt-r2.17-dev.conllu'
    manifest = {'scope': 'modern engineering build/score only; no decipherment or final benchmark',
                'config': asdict(ModelConfig()), 'sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (train, dev)},
                'inventory_policy': 'Normalized training forms only; dev never adds forms'}
    (output / 'protocol.json').write_text(json.dumps(manifest, indent=2) + '\n')
    inventory = Inventory.build(output / 'inventory.sqlite', (w for d in documents(train) for w in d.words))
    inventory_seconds = time.perf_counter() - started
    lm_started = time.perf_counter()
    model = SparseBigram.train(inventory, ((inventory.id(w) for w in d.words) for d in documents(train)))
    model.save(output / 'model.sqlite')
    lm_seconds = time.perf_counter() - lm_started
    restored = SparseBigram.load(output / 'model.sqlite', inventory)
    dev_docs, dev_tokens, missing_tokens, covered_docs, covered_tokens = 0, 0, 0, 0, 0
    genuine, shuffled, events = 0., 0., 0
    rng = random.Random(17)
    for doc in documents(dev):
        dev_docs += 1
        dev_tokens += len(doc.words)
        ids, missing = [], 0
        for word in doc.words:
            try:
                ids.append(inventory.id(word))
            except KeyError:
                missing += 1
        missing_tokens += missing
        if missing:
            continue  # Explicitly counted coverage exclusion, never join a gap.
        covered_docs += 1
        covered_tokens += len(ids)
        score = model.score(ids)
        assert score == restored.score_chunks((ids[:3], ids[3:]))
        genuine += score
        rng.shuffle(ids)
        shuffled += model.score(ids)
        events += len(ids) + 1
    # ru_maxrss is bytes on macOS, KiB on Linux; label the platform explicitly.
    maximum = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = maximum if sys.platform == 'darwin' else maximum * 1024
    report = {**manifest, 'inventory_forms': inventory.size, 'inventory_sha256': inventory.identity,
              'model_sha256': model.identity, 'observed_edges': len(model.edges),
              'training_tokens': sum(model.counts[:-1]), 'training_documents': model.counts[-1],
              'inventory_seconds': inventory_seconds, 'model_build_save_seconds': lm_seconds,
              'elapsed_seconds': time.perf_counter() - started,
              'peak_process_rss_bytes': peak_bytes, 'platform': sys.platform,
              'inventory_bytes': (output / 'inventory.sqlite').stat().st_size,
              'model_bytes': (output / 'model.sqlite').stat().st_size,
              'development': {'documents': dev_docs, 'tokens': dev_tokens, 'missing_tokens': missing_tokens,
                              'fully_covered_documents': covered_docs, 'scored_tokens': covered_tokens,
                              'excluded_documents': dev_docs - covered_docs,
                              'genuine_nats_per_event': -genuine/events if events else None,
                              'shuffled_nats_per_event': -shuffled/events if events else None},
              'limitations': ['EWT standard splits are not verified author-disjoint.',
                              'Loss covers only fully admitted development documents; exclusions remain explicit.',
                              'Python edge/count dictionaries and identity hashing have non-packed overhead.',
                              'No million-form allocation or decipherment run was attempted.',
                              'ASCII scoring tokenization is lossy and not UD syntactic token alignment.']}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    inventory.close()
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=Path('data/raw/scalable-english'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    args = parser.parse_args()
    print(json.dumps(build(args.raw_dir, args.output), indent=2))
