"""One frozen length-eight replay with durable phase timings."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import z3
from benchmarks import latin_layered_lengths as baseline
from benchmarks import latin_compact_membership as compact
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.layered_membership import layered_membership

OUT = Path('experiments/results/latin-layered-timeout')


def prepare():
    source = baseline.prepare()
    matches = [(i, case) for i, case in enumerate(source['cases'])
               if case['mode'] == 'upstream-default' and case['length'] == 8 and case['kind'] == 'hidden-word']
    assert len(matches) == 1
    index, case = matches[0]
    p = {'baseline_sha256': digest(source), 'baseline_case': index, 'case': case,
         'code_sha256': digest(Path(__file__).read_text()), 'encoding_sha256': source['encoding_sha256'],
         'solver_ms': 30000, 'worker_wall_seconds': 60,
         'scope': 'Single previously UNKNOWN default length-eight positive. Same query and encoding; only budget and durable phase instrumentation changed. No retry or cipher recovery.'}
    path = OUT / 'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p
    else: write_json(path, p)
    return p


def worker():
    p = json.loads((OUT / 'prepared.json').read_text()); case = p['case']; timings = {}
    total = perf_counter()
    def checkpoint(phase):
        write_json(OUT / 'phases.json', {'prepared_sha256': digest(p), 'phase': phase,
                                        'timings': timings, 'worker_elapsed_seconds': perf_counter() - total})
    checkpoint('loading'); start = perf_counter()
    a = compact.load_automaton(case['automaton']); alphabet = Alphabet(tuple(case['alphabet']['symbols']))
    timings['load_seconds'] = perf_counter() - start
    checkpoint('constructing'); start = perf_counter()
    symbols = [z3.Int(f'letter{i}') for i in range(case['length'])]
    solver = z3.Solver(); solver.set(timeout=p['solver_ms'])
    formula, _, edges = layered_membership(a, alphabet, symbols, 'word'); solver.add(formula)
    timings['construction_seconds'] = perf_counter() - start
    checkpoint('solving'); start = perf_counter(); status = solver.check()
    timings['solver_seconds'] = perf_counter() - start
    row = {'status': str(status).upper(), 'verified': False, 'layer_edges': edges}
    checkpoint('verifying'); start = perf_counter()
    if status == z3.sat:
        model = solver.model(); word = ''.join(alphabet.symbols[model.eval(s).as_long()] for s in symbols)
        assert len(word) == case['length'] and a.accepts(word)
        row.update(word=word, verified=True)
    elif status == z3.unknown: row['reason'] = solver.reason_unknown()
    timings['verification_seconds'] = perf_counter() - start
    row.update(timings=timings, worker_elapsed_seconds=perf_counter() - total)
    write_json(OUT / 'result.json', row); checkpoint('complete')


def run():
    p = prepare()
    if not (OUT / 'result.json').exists():
        start = perf_counter()
        try:
            result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_layered_timeout', '--worker'],
                                    capture_output=True, text=True, timeout=p['worker_wall_seconds'])
            if result.returncode: raise RuntimeError(result.stderr[-2000:])
        except subprocess.TimeoutExpired:
            write_json(OUT / 'result.json', {'status': 'WALL_TIMEOUT', 'verified': False,
                                            'wall_seconds': perf_counter() - start})
    row = json.loads((OUT / 'result.json').read_text())
    write_json(OUT / 'report.json', {'prepared_sha256': digest(p), 'complete': True, 'result': row})
    print(row, flush=True)


def validate():
    p = prepare(); report = json.loads((OUT / 'report.json').read_text())
    row = json.loads((OUT / 'result.json').read_text()); phase = json.loads((OUT / 'phases.json').read_text())
    assert report['complete'] and report['prepared_sha256'] == digest(p) and report['result'] == row
    assert phase['prepared_sha256'] == digest(p) and row['status'] in ('SAT', 'UNKNOWN', 'WALL_TIMEOUT')
    if row['status'] != 'WALL_TIMEOUT':
        assert phase['phase'] == 'complete' and phase['timings'] == row['timings']
        assert all(value >= 0 for value in row['timings'].values())
    if row['status'] == 'SAT':
        assert row['verified'] and len(row['word']) == p['case']['length']
        assert compact.load_automaton(p['case']['automaton']).accepts(row['word'])
    write_json(OUT / 'validation.json', {'verified': True, 'cases': 1})
    print('Validated longer-budget membership replay')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', action='store_true'); args = parser.parse_args()
    if args.worker: worker()
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
