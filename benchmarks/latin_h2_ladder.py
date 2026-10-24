"""Frozen nested vocabulary ladder for the assisted H2 fixture."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_pool as engine
from benchmarks import latin_compact_membership as compact
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.word_automaton import WordAutomaton

OUT = Path('experiments/results/latin-h2-ladder')
SIZES = (512, 1024, 2048, 4096, 8192, 16384, 32768)
EXTENSION_SEED = 6201


def nested_words(pool, eligible, sizes=SIZES):
    base = set(pool)
    extension = sorted(set(eligible) - base)
    random.Random(EXTENSION_SEED).shuffle(extension)
    assert all(len(base) <= size <= len(base) + len(extension) for size in sizes)
    return [sorted(base | set(extension[:size-len(base)])) for size in sizes]


def prepare():
    source = engine.prepare()
    fixture = source['fixtures'][0]
    pool = list(compact.inventory_lines(fixture['inventory']['path']))
    full = compact.prepare()['inventories']['upstream-default']['inventory']
    eligible = [w for w in compact.inventory_lines(full['path']) if 3 <= len(w) <= 6]
    rungs = []
    for size, words in zip(SIZES, nested_words(pool, eligible)):
        folder = OUT / str(size)
        folder.mkdir(parents=True, exist_ok=True)
        metadata = []
        for name, raw in [('inventory.txt.gz', gzip.compress(('\n'.join(words)+'\n').encode(), mtime=0)),
                          ('automaton.json.gz', gzip.compress(json.dumps(asdict(WordAutomaton.from_sorted(words)), separators=(',', ':')).encode(), mtime=0))]:
            path = folder / name
            if path.exists(): assert path.read_bytes() == raw
            else: path.write_bytes(raw)
            metadata.append({'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()})
        inventory, automaton = metadata
        inventory['word_count'] = size
        changed = {**fixture, 'inventory': inventory, 'case': {**fixture['case'], 'automaton': automaton}}
        rungs.append({'size': size, 'fixtures': [changed]})
    p = {'baseline_sha256': digest(source), 'code_sha256': {str(Path(__file__)): digest(Path(__file__).read_text()),
         str(Path(engine.__file__)): digest(Path(engine.__file__).read_text())},
         'extension_seed': EXTENSION_SEED, 'eligible_count': len(eligible), 'rungs': rungs,
         'scope': 'Assisted nested vocabulary diagnostic: original sampling pool retained; independent extension order; identical cipher, key, holdout, scoring and 30s solver/60s worker budgets. Seven frozen sizes, one fixture, no manuscript inference.'}
    path = OUT / 'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p
    else: write_json(path, p)
    return p


def worker(size, arm):
    p = json.loads((OUT / 'prepared.json').read_text())
    rung = next(r for r in p['rungs'] if r['size'] == size)
    engine.OUT = OUT / str(size) / rung['fixtures'][0]['id']
    engine.fit(arm)


def run():
    p = prepare()
    for rung in p['rungs']:
        size = rung['size']; fixture = rung['fixtures'][0]
        root = OUT / str(size); folder = root / fixture['id']
        write_json(folder / 'prepared.json', fixture)
        rows = {}
        for arm in fixture['arms']:
            path = folder / f'{arm}-result.json'
            print(f'Vocabulary {size}: {arm}', flush=True)
            if not path.exists():
                start = perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_h2_ladder', '--worker', str(size), '--arm', arm], capture_output=True, text=True, timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter()-start})
            rows[arm] = json.loads(path.read_text())
            row = rows[arm]
            print(row['status'], 'solver=', row.get('timings', {}).get('solver_seconds'), 'held_exact=', row.get('held_exact'), flush=True)
        write_json(root / 'report.json', {'prepared_sha256': digest(rung), 'complete': True, 'fixtures': {fixture['id']: rows}})
    validate()


def validate():
    p = prepare()
    original_out, original_prepare = engine.OUT, engine.prepare
    try:
        for rung in p['rungs']:
            engine.OUT = OUT / str(rung['size'])
            engine.prepare = lambda rung=rung: rung
            engine.validate()
    finally:
        engine.OUT, engine.prepare = original_out, original_prepare
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
