"""Bounded standalone queries against frozen full Latin automata."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter
import z3
from benchmarks import latin_compact_membership as compact
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.layered_membership import layered_membership
from benchmarks import latin_symbolic_membership as baseline

OUT = Path('experiments/results/latin-layered-membership')
SOLVER_MS = 2000
WALL_SECONDS = 15


def prepare():
    original = baseline.prepare()
    p = {'baseline_prepared_sha256': digest(original),
         'code_sha256': digest(Path(__file__).read_text()),
         'encoding_sha256': digest(Path('src/voynich_smt/solver/layered_membership.py').read_text()),
         'solver_ms': original['solver_ms'], 'worker_wall_seconds': original['worker_wall_seconds'],
         'cases': original['cases'],
         'scope': 'Same six fixed-length queries and budgets as constant-array baseline; exact sparse transitions pruned only by public length and root reachability. No cipher recovery.'}
    path = OUT / 'prepared.json'
    if path.exists():
        assert json.loads(path.read_text()) == p, 'Frozen benchmark changed'
    else:
        write_json(path, p)
    return p


def worker(index):
    p = json.loads((OUT / 'prepared.json').read_text()); case = p['cases'][index]
    a = compact.load_automaton(case['automaton']); alphabet = Alphabet(tuple(case['alphabet']['symbols']))
    start = perf_counter()
    symbols = z3.Ints('letter0 letter1 letter2 letter3 letter4')
    solver = z3.Solver(); solver.set(timeout=p['solver_ms'])
    formula, states, edge_counts = layered_membership(a, alphabet, symbols, 'word')
    solver.add(formula)
    for i, symbol in enumerate(symbols):
        if case['kind'] == 'concrete' or (case['kind'] == 'one-hidden-letter' and i != 2):
            solver.add(symbol == alphabet.index(case['anchor'][i]))
    construction = perf_counter() - start
    start = perf_counter(); status = solver.check(); seconds = perf_counter() - start
    row = {'case': index, 'status': str(status).upper(), 'construction_seconds': construction,
           'solver_seconds': seconds, 'verified': False, 'layer_edges': edge_counts}
    if status == z3.sat:
        model = solver.model(); word = ''.join(alphabet.symbols[model.eval(s).as_long()] for s in symbols)
        assert a.accepts(word) and len(word) == 5
        assert case['kind'] != 'concrete' or word == case['anchor']
        assert case['kind'] != 'one-hidden-letter' or all(word[i] == case['anchor'][i] for i in (0, 1, 3, 4))
        row.update(word=word, verified=True)
    elif status == z3.unknown:
        row['reason'] = solver.reason_unknown()
    write_json(OUT / f'case-{index}.json', row)


def run():
    p = prepare()
    for i, case in enumerate(p['cases']):
        path = OUT / f'case-{i}.json'
        if path.exists(): continue
        print(case['mode'], case['kind'], flush=True)
        start = perf_counter()
        try:
            result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_layered_membership', '--worker', str(i)],
                                    capture_output=True, text=True, timeout=p['worker_wall_seconds'])
            if result.returncode:
                raise RuntimeError(result.stderr[-2000:])
        except subprocess.TimeoutExpired:
            write_json(path, {'case': i, 'status': 'WALL_TIMEOUT', 'verified': False,
                              'wall_seconds': perf_counter() - start})
        print(json.loads(path.read_text()), flush=True)
    rows = [json.loads((OUT / f'case-{i}.json').read_text()) for i in range(len(p['cases']))]
    write_json(OUT / 'report.json', {'prepared_sha256': digest(p), 'complete': True, 'rows': rows})


def validate():
    p = prepare(); r = json.loads((OUT / 'report.json').read_text())
    assert r['complete'] and r['prepared_sha256'] == digest(p)
    assert len(r['rows']) == len(p['cases'])
    for i, row in enumerate(r['rows']):
        assert row == json.loads((OUT / f'case-{i}.json').read_text()) and row['case'] == i
        assert row['status'] in ('SAT', 'UNKNOWN', 'WALL_TIMEOUT')  # Every case has the known anchor witness.
        if row['status'] == 'SAT':
            case = p['cases'][i]; word = row['word']
            assert row['verified'] and compact.load_automaton(case['automaton']).accepts(word) and len(word) == 5
            assert case['kind'] != 'concrete' or word == case['anchor']
            assert case['kind'] != 'one-hidden-letter' or all(word[j] == case['anchor'][j] for j in (0, 1, 3, 4))
    write_json(OUT / 'validation.json', {'verified': True, 'cases': len(r['rows'])})
    print('Validated sparse layered membership records')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', type=int)
    args = parser.parse_args()
    if args.worker is not None: worker(args.worker)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
