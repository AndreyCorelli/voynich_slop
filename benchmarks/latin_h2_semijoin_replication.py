"""Frozen pairwise-support refinement of two H2 vocabulary rungs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_public as baseline
from benchmarks.latin_h2_ladder import nested_words
from benchmarks import latin_compact_membership as compact
from voynich_smt.language.word_automaton import WordAutomaton
from dataclasses import asdict
import gzip
import hashlib
import random
from benchmarks import latin_h2_pool as engine
from voynich_smt.solver import candidate_semijoin as capacity_matching
from voynich_smt.data.corpus import digest, write_json

OUT = Path('experiments/results/latin-h2-semijoin-replication')
SEEDS = (5102, 5103)
VOCABULARY_SIZE = 16384


def prepare():
    source = baseline.prepare()
    full = compact.prepare()['inventories']['upstream-default']['inventory']
    eligible = [w for w in compact.inventory_lines(full['path']) if 3 <= len(w) <= 6]
    rungs = []
    for fixture in source['fixtures'][1:]:
        seed = int(fixture['id'].split('-')[-1]); assert seed in SEEDS
        pool = sorted(random.Random(seed).sample(eligible, 512))
        words = nested_words(pool, eligible, (VOCABULARY_SIZE,))[0]
        assert set(fixture['truth']['train'] + fixture['truth']['held']) <= set(pool)
        folder = OUT / str(seed); folder.mkdir(parents=True, exist_ok=True)
        metadata = []
        for name, raw in [('inventory.txt.gz', gzip.compress(('\n'.join(words)+'\n').encode(), mtime=0)),
                          ('automaton.json.gz', gzip.compress(json.dumps(asdict(WordAutomaton.from_sorted(words)), separators=(',', ':')).encode(), mtime=0))]:
            path = folder / name
            if path.exists(): assert path.read_bytes() == raw
            else: path.write_bytes(raw)
            metadata.append({'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()})
        inventory, automaton = metadata; inventory['word_count'] = VOCABULARY_SIZE
        changed = {**fixture, 'inventory': inventory, 'case': {**fixture['case'], 'automaton': automaton}}
        rungs.append({'seed': seed, 'vocabulary_size': VOCABULARY_SIZE, 'fixtures': [changed]})
    p = {'baseline_sha256': digest(source), 'rungs': rungs,
         'code_sha256': {str(path): digest(path.read_text()) for path in (Path(__file__), Path(engine.__file__), Path(capacity_matching.__file__), Path('src/voynich_smt/solver/capacity_matching.py'))},
         'scope': 'Replication on original independent H2 synthetic seeds 5102/5103; each original whole sampling pool retained with independent extension order 6201 to 16384 words. Same budgets/scoring and matching plus semijoin method. No individual truth additions or fixture replacements.'}
    path = OUT / 'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p
    else: write_json(path, p)
    return p


def configure(root):
    engine.OUT = root
    engine.propagate_candidates = capacity_matching.propagate_candidates


def worker(size, arm):
    p = json.loads((OUT / 'prepared.json').read_text())
    rung = next(r for r in p['rungs'] if r['seed'] == size)
    configure(OUT / str(size) / rung['fixtures'][0]['id'])
    engine.fit(arm)


def run():
    p = prepare()
    for rung in p['rungs']:
        size = rung['seed']; fixture = rung['fixtures'][0]
        root = OUT / str(size); folder = root / fixture['id']
        write_json(folder / 'prepared.json', fixture)
        rows = {}
        for arm in fixture['arms']:
            path = folder / f'{arm}-result.json'
            print(f'Fixture {size}, vocabulary 16384: {arm}', flush=True)
            if not path.exists():
                start = perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_h2_semijoin_replication', '--worker', str(size), '--arm', arm], capture_output=True, text=True, timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter()-start})
            rows[arm] = json.loads(path.read_text())
            print(rows[arm]['status'], rows[arm].get('timings'), 'held=', rows[arm].get('held_exact'), flush=True)
        write_json(root / 'report.json', {'prepared_sha256': digest(rung), 'complete': True, 'fixtures': {fixture['id']: rows}})
    validate()


def validate():
    p = prepare()
    old = engine.OUT, engine.prepare, engine.propagate_candidates
    try:
        for rung in p['rungs']:
            configure(OUT / str(rung['seed']))
            engine.prepare = lambda rung=rung: rung
            engine.validate()
    finally:
        engine.OUT, engine.prepare, engine.propagate_candidates = old
    write_json(OUT / 'validation.json', {'verified': True, 'rungs': len(p['rungs']), 'arms': 2*len(p['rungs'])})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', type=int); parser.add_argument('--arm', choices=['positive', 'shuffle'])
    args = parser.parse_args()
    if args.worker is not None: worker(args.worker, args.arm)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
