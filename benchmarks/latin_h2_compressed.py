"""Frozen pairwise-support refinement of two H2 vocabulary rungs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_ladder as baseline
from benchmarks import latin_h2_pool as engine
from voynich_smt.solver import candidate_semijoin as capacity_matching
from voynich_smt.solver.compressed_candidates import compressed_membership
from voynich_smt.data.corpus import digest, write_json

OUT = Path('experiments/results/latin-h2-compressed')
SIZES = (8192, 16384)


def prepare():
    source = baseline.prepare()
    p = {'baseline_sha256': digest(source), 'rungs': [{**r, 'mode': mode, 'job': f"{mode}-{r['size']}"} for mode in ('layered','dag','defined') for r in source['rungs'] if r['size'] in (16384,32768)],
         'code_sha256': {str(path): digest(path.read_text()) for path in (Path(__file__), Path(capacity_matching.__file__), Path('src/voynich_smt/solver/capacity_matching.py'), Path('src/voynich_smt/solver/compressed_candidates.py'))},
         'scope': 'Same frozen H2 ladder inputs, first-key scoring and budgets; matching-capacity filtering plus pairwise candidate semijoins on at least two shared codes. Three compressed membership encodings, unchanged Boolean inverse, one fixture, assisted vocabulary.'}
    path = OUT / 'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p
    else: write_json(path, p)
    return p


def configure(root, mode):
    engine.OUT = root
    engine.propagate_candidates = capacity_matching.propagate_candidates
    counter = iter(range(1000000))
    engine.candidate_membership = lambda letters, cipher, candidates, equalities: compressed_membership(cipher, candidates, equalities, f'word_{next(counter)}', mode)


def worker(size, arm):
    p = json.loads((OUT / 'prepared.json').read_text())
    rung = next(r for r in p['rungs'] if r['job'] == size)
    configure(OUT / str(size) / rung['fixtures'][0]['id'], rung['mode'])
    engine.fit(arm)


def run():
    p = prepare()
    for rung in p['rungs']:
        size = rung['job']; fixture = rung['fixtures'][0]
        root = OUT / str(size); folder = root / fixture['id']
        write_json(folder / 'prepared.json', fixture)
        rows = {}
        for arm in fixture['arms']:
            path = folder / f'{arm}-result.json'
            print(f'Vocabulary {size}: {arm}', flush=True)
            if not path.exists():
                start = perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_h2_compressed', '--worker', str(size), '--arm', arm], capture_output=True, text=True, timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter()-start})
            rows[arm] = json.loads(path.read_text())
            print(rows[arm]['status'], rows[arm].get('timings'), 'held=', rows[arm].get('held_exact'), flush=True)
        write_json(root / 'report.json', {'prepared_sha256': digest(rung), 'complete': True, 'fixtures': {fixture['id']: rows}})
    validate()


def validate():
    p = prepare()
    old = engine.OUT, engine.prepare, engine.propagate_candidates, engine.candidate_membership
    try:
        for rung in p['rungs']:
            configure(OUT / rung['job'], rung['mode'])
            engine.prepare = lambda rung=rung: rung
            engine.validate()
    finally:
        engine.OUT, engine.prepare, engine.propagate_candidates, engine.candidate_membership = old
    write_json(OUT / 'validation.json', {'verified': True, 'rungs': len(p['rungs']), 'arms': 2*len(p['rungs'])})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker'); parser.add_argument('--arm', choices=['positive', 'shuffle'])
    args = parser.parse_args()
    if args.worker is not None: worker(args.worker, args.arm)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
