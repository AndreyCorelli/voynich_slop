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
from benchmarks import latin_layered_membership as baseline
from itertools import product

OUT = Path('experiments/results/latin-layered-lengths')
SOLVER_MS = 2000
WALL_SECONDS = 15


def prepare():
    original = baseline.prepare()
    report = json.loads((compact.OUT / 'report.json').read_text())
    source = compact.prepare()
    lengths = (2, 5, 8, 12)
    cases = []
    for mode, row in report['modes'].items():
        metadata = source['inventories'][mode]['inventory']
        import hashlib
        assert hashlib.sha256(Path(metadata['path']).read_bytes()).hexdigest() == metadata['sha256']
        anchors = {}; prefixes = {length: set() for length in lengths}
        for word in compact.inventory_lines(metadata['path']):
            if len(word) in prefixes:
                anchors.setdefault(len(word), word)
                prefixes[len(word)].add(word[:2])
        for length in lengths:
            absent = next(''.join(pair) for pair in product(row['alphabet']['symbols'], repeat=2)
                          if ''.join(pair) not in prefixes[length])
            for kind in ('hidden-word', 'impossible-prefix'):
                cases.append({'mode': mode, 'kind': kind, 'length': length,
                              'anchor': anchors[length], 'prefix': absent if kind == 'impossible-prefix' else '',
                              'expected': 'UNSAT' if kind == 'impossible-prefix' else 'SAT',
                              'automaton': row['automaton'], 'alphabet': row['alphabet']})
    p = {'baseline_prepared_sha256': digest(original),
         'code_sha256': digest(Path(__file__).read_text()),
         'encoding_sha256': digest(Path('src/voynich_smt/solver/layered_membership.py').read_text()),
         'solver_ms': original['solver_ms'], 'worker_wall_seconds': original['worker_wall_seconds'],
         'cases': cases, 'lengths': list(lengths),
         'scope': 'Frozen lengths 2,5,8,12; all letters hidden or lexicographically first absent two-letter prefix at that length, established by exact inventory scan. Same budgets; no cipher recovery.'}
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
    symbols = [z3.Int(f'letter{i}') for i in range(case['length'])]
    solver = z3.Solver(); solver.set(timeout=p['solver_ms'])
    formula, states, edge_counts = layered_membership(a, alphabet, symbols, 'word')
    solver.add(formula)
    for symbol, letter in zip(symbols, case['prefix']):
        solver.add(symbol == alphabet.index(letter))
    construction = perf_counter() - start
    start = perf_counter(); status = solver.check(); seconds = perf_counter() - start
    row = {'case': index, 'status': str(status).upper(), 'construction_seconds': construction,
           'solver_seconds': seconds, 'verified': False, 'layer_edges': edge_counts}
    if status == z3.sat:
        model = solver.model(); word = ''.join(alphabet.symbols[model.eval(s).as_long()] for s in symbols)
        assert a.accepts(word) and len(word) == case['length'] and word.startswith(case['prefix'])
        row.update(word=word, verified=True)
    elif status == z3.unknown:
        row['reason'] = solver.reason_unknown()
    write_json(OUT / f'case-{index}.json', row)


def run():
    p = prepare()
    for i, case in enumerate(p['cases']):
        path = OUT / f'case-{i}.json'
        if path.exists(): continue
        print(case['mode'], case['length'], case['kind'], flush=True)
        start = perf_counter()
        try:
            result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_layered_lengths', '--worker', str(i)],
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
        case = p['cases'][i]
        assert row['status'] in (case['expected'], 'UNKNOWN', 'WALL_TIMEOUT')
        if row['status'] == 'SAT':
            word = row['word']
            assert row['verified'] and compact.load_automaton(case['automaton']).accepts(word)
            assert len(word) == case['length'] and word.startswith(case['prefix'])
    # Recheck expectations independently against exact generated inventories.
    source = compact.prepare()
    for mode in source['inventories']:
        subset = [case for case in p['cases'] if case['mode'] == mode]
        found = set()
        for word in compact.inventory_lines(source['inventories'][mode]['inventory']['path']):
            for j, case in enumerate(subset):
                if len(word) == case['length'] and word.startswith(case['prefix']): found.add(j)
        assert found == {j for j, case in enumerate(subset) if case['expected'] == 'SAT'}
    write_json(OUT / 'validation.json', {'verified': True, 'cases': len(r['rows'])})
    print('Validated length-range membership records')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', type=int)
    args = parser.parse_args()
    if args.worker is not None: worker(args.worker)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
