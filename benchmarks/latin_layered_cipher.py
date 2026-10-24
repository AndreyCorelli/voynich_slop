"""One frozen length-eight replay with durable phase timings."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import z3
from benchmarks import latin_layered_timeout as baseline
import random
from itertools import product
from benchmarks import latin_compact_membership as compact
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.layered_membership import layered_membership

OUT = Path('experiments/results/latin-layered-cipher')


def prepare():
    source = baseline.prepare(); case = source['case']
    a = compact.load_automaton(case['automaton'])
    train = ['amare', 'arma', 'mare']; held = 'area'
    assert all(a.accepts(w) for w in train + [held])
    assert held not in train and set(held) <= set(''.join(train))
    pool = [''.join(pair) for pair in product('uvwxyz', repeat=2)]
    random.Random(4901).shuffle(pool)
    key = dict(zip(case['alphabet']['symbols'], pool))
    encrypt = lambda word: [key[letter] for letter in word]
    p = {'baseline_sha256': digest(source), 'case': case,
         'code_sha256': digest(Path(__file__).read_text()), 'encoding_sha256': source['encoding_sha256'],
         'solver_ms': 30000, 'worker_wall_seconds': 60,
         'train_cipher': [encrypt(w) for w in train], 'held_cipher': encrypt(held),
         'truth': {'train': train, 'held': held, 'key': key}, 'seed': 4901,
         'scope': 'One default-inventory synthetic control; three hidden training words, one frozen novel code-covered held-out word. Public fixed two-glyph boundaries/word lengths, H1 injective substitution. No true letters/key supplied to solving; no manuscript fit or randomized control.'}
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
    observed = sorted({code for word in p['train_cipher'] for code in word})
    letters = {code: z3.Int(f'key_{i}') for i, code in enumerate(observed)}
    solver = z3.Solver(); solver.set(timeout=p['solver_ms'])
    solver.add(z3.Distinct(list(letters.values())))
    solver.add([z3.And(letter >= 0, letter < len(alphabet.symbols)) for letter in letters.values()])
    edges = []
    for i, word in enumerate(p['train_cipher']):
        formula, _, counts = layered_membership(a, alphabet, [letters[c] for c in word], f'word_{i}')
        solver.add(formula); edges.append(counts)
    timings['construction_seconds'] = perf_counter() - start
    checkpoint('solving'); start = perf_counter(); status = solver.check()
    timings['solver_seconds'] = perf_counter() - start
    row = {'status': str(status).upper(), 'verified': False, 'layer_edges': edges}
    checkpoint('verifying'); start = perf_counter()
    if status == z3.sat:
        model = solver.model()
        recovered = {code: alphabet.symbols[model.eval(letter).as_long()] for code, letter in letters.items()}
        decode = lambda codes: ''.join(recovered[code] for code in codes)
        words = [decode(word) for word in p['train_cipher']]
        assert len(set(recovered.values())) == len(recovered)
        assert all(a.accepts(word) and len(word) == len(cipher) for word, cipher in zip(words, p['train_cipher']))
        held = decode(p['held_cipher'])
        row.update(verified=True, recovered_key=recovered, training_words=words,
                   training_exact=sum(w == t for w, t in zip(words, p['truth']['train'])),
                   held_word=held, held_exact=held == p['truth']['held'], held_member=a.accepts(held))
    elif status == z3.unknown: row['reason'] = solver.reason_unknown()
    timings['verification_seconds'] = perf_counter() - start
    row.update(timings=timings, worker_elapsed_seconds=perf_counter() - total)
    write_json(OUT / 'result.json', row); checkpoint('complete')


def run():
    p = prepare()
    if not (OUT / 'result.json').exists():
        start = perf_counter()
        try:
            result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_layered_cipher', '--worker'],
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
        a = compact.load_automaton(p['case']['automaton']); key = row['recovered_key']
        decode = lambda word: ''.join(key[c] for c in word)
        assert row['verified'] and len(set(key.values())) == len(key)
        words = [decode(word) for word in p['train_cipher']]
        assert words == row['training_words'] and all(a.accepts(w) for w in words)
        assert row['training_exact'] == sum(w == t for w, t in zip(words, p['truth']['train']))
        held = decode(p['held_cipher'])
        assert held == row['held_word'] and row['held_exact'] == (held == p['truth']['held'])
        assert row['held_member'] == a.accepts(held)
    write_json(OUT / 'validation.json', {'verified': True, 'cases': 1})
    print('Validated shared-key synthetic control')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', action='store_true'); args = parser.parse_args()
    if args.worker: worker()
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
