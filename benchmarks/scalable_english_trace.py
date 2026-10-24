"""Public-only observational replay of an existing fixed search trajectory.

Adds no proposals and uses no truth. Pool and move events stream to gzip so
post-hoc evaluation can distinguish missing candidates from ranking/acceptance.
"""
from contextlib import contextmanager
import argparse
import gzip
import json
from pathlib import Path
import time

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
from voynich_smt.word_mapping.scalable.search import DictionarySearch, SearchConfig
from voynich_smt.word_mapping.scalable.trigram import load_model


@contextmanager
def observe(search, write):
    """Observe without altering RNG calls, candidate scores or decisions."""
    original_advance = search.advance
    original_refresh = search.retriever.refresh
    def refresh(cipher, *, audit=None):
        captured = []
        def capture(candidates):
            captured.extend((c.word_id, c.log_delta) for c in candidates)
            if audit is not None:
                audit(candidates)
        row = original_refresh(cipher, audit=capture)
        write({'kind': 'pool', 'step': search.step + 1, 'cipher': cipher,
               'generation': row.generation, 'offered': captured,
               'active': [c.word_id for c in row.candidates]})
        return row
    search.retriever.refresh = refresh
    write({'kind': 'initial', 'assignments': search.scorer.state.assignments})
    def advance():
        event = original_advance()
        cipher, word, move = search._last_proposal
        assert cipher == event['cipher']
        write({'kind': 'move', **event, 'word_id': word, 'changes': move.changes})
        return event
    search.advance = advance
    try:
        yield
    finally:
        search.advance = original_advance
        search.retriever.refresh = original_refresh


def replay(search, steps, write):
    """Observe without altering RNG calls, candidate scores or decisions."""
    next_update = time.monotonic() + 30
    with observe(search, write):
        for _ in range(steps):
            search.advance()
            if time.monotonic() >= next_update:
                print(json.dumps({'seed': search.seed, 'step': search.step, 'scope': 'observational replay'}), flush=True)
                next_update = time.monotonic() + 30
        search.scorer.validate()


def run(resources, root, output):
    inference = json.loads((root / 'inference.json').read_text())
    protocol = inference['protocol']
    stream = CipherStream.load(root / 'public/cipher.json')
    output.mkdir(parents=True, exist_ok=False)
    inventory = Inventory(resources / 'inventory.sqlite')
    try:
        model = load_model(resources / 'model.sqlite', inventory)
        assert protocol['model_sha256'] == model.identity and protocol['cipher_sha256'] == stream.identity
        reports = []
        for expected in inference['runs']:
            seed = expected['seed']
            search = DictionarySearch(model, stream, seed=seed,
                                      config=SearchConfig(**protocol['search']),
                                      retrieval_config=RetrievalConfig(**protocol['retrieval']))
            path = output / f'seed-{seed}.jsonl.gz'
            started = time.perf_counter()
            with gzip.open(path, 'wt', encoding='utf-8') as handle:
                replay(search, expected['step'], lambda event: handle.write(json.dumps(event, separators=(',', ':')) + '\n'))
            assert abs(search.scorer.score - expected['current_score']) < 1e-8
            actual = [{'score': score, 'assignments': list(key)} for score, key in search.joint_archive]
            assert actual == expected['joint_archive'], 'Instrumented trajectory differs from saved run'
            reports.append({'seed': seed, 'steps': search.step, 'exact_joint_archive_match': True,
                            'trace': path.name, 'compressed_bytes': path.stat().st_size,
                            'elapsed_seconds': time.perf_counter() - started})
            print(json.dumps(reports[-1]), flush=True)
        result = {'scope': 'observational replay, not new inference evidence', 'protocol': protocol, 'runs': reports}
        (output / 'trace-report.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--run', type=Path, default=Path('experiments/results/scalable-english/search-ewt-v1'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/scalable-english/search-ewt-diagnostics-v1/traces'))
    args = parser.parse_args()
    run(args.resources, args.run, args.output)
