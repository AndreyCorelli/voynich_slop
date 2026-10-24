"""One frozen length-eight replay with durable phase timings."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import z3
from benchmarks import latin_layered_cipher as baseline
import random
from itertools import product
from benchmarks import latin_compact_membership as compact
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.layered_membership import layered_membership

OUT = Path('experiments/results/latin-layered-diversity')


def prepare():
    source = baseline.prepare(); case = source['case']
    metadata = compact.prepare()['inventories']['upstream-default']['inventory']
    rng = random.Random(5001); reservoir = []; count = 0
    for word in compact.inventory_lines(metadata['path']):
        if not 3 <= len(word) <= 6: continue
        count += 1
        if len(reservoir) < 512: reservoir.append(word)
        else:
            slot = rng.randrange(count)
            if slot < 512: reservoir[slot] = word
    remaining = sorted(reservoir); train = []; covered = set()
    for _ in range(12):
        word = min(remaining, key=lambda w: (-len(set(w) - covered), w))
        train.append(word); covered.update(word); remaining.remove(word)
    held = [w for w in remaining if set(w) <= covered][:3]
    assert len(held) == 3 and not set(held) & set(train)
    key = source['truth']['key']; encrypt = lambda word: [key[c] for c in word]
    positive = [encrypt(w) for w in train]
    flat = [c for word in positive for c in word]
    random.Random(5002).shuffle(flat)
    shuffled = []; offset = 0
    for word in positive:
        shuffled.append(flat[offset:offset + len(word)]); offset += len(word)
    assert shuffled != positive
    p = {'baseline_sha256': digest(source), 'case': case,
         'code_sha256': digest(Path(__file__).read_text()), 'encoding_sha256': source['encoding_sha256'],
         'solver_ms': 30000, 'worker_wall_seconds': 60,
         'arms': {'positive': positive, 'shuffle': shuffled},
         'held_cipher': [encrypt(w) for w in held],
         'truth': {'train': train, 'held': held, 'key': key},
         'selection': {'seed': 5001, 'pool_size': 512, 'eligible_count': count,
                       'lengths': [3,6], 'covered_letters': sorted(covered), 'shuffle_seed': 5002},
         'scope': 'Twelve diverse generated-inventory words chosen by reservoir then greedy new-letter coverage, three novel covered holdouts. Same key as prior toy. Public fixed-two codes and lengths. Global atomic-code shuffle preserves per-word lengths and global code counts, not word equality partitions; it can admit a fit. One first-key fit per arm, no retries.'}
    path = OUT / 'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p
    else: write_json(path, p)
    return p


def worker(arm):
    p = json.loads((OUT / 'prepared.json').read_text()); case = p['case']; timings = {}; train_cipher = p['arms'][arm]
    total = perf_counter()
    def checkpoint(phase):
        write_json(OUT / f'{arm}-phases.json', {'prepared_sha256': digest(p), 'phase': phase,
                                        'timings': timings, 'worker_elapsed_seconds': perf_counter() - total})
    checkpoint('loading'); start = perf_counter()
    a = compact.load_automaton(case['automaton']); alphabet = Alphabet(tuple(case['alphabet']['symbols']))
    timings['load_seconds'] = perf_counter() - start
    checkpoint('constructing'); start = perf_counter()
    observed = sorted({code for word in train_cipher for code in word})
    letters = {code: z3.Int(f'key_{i}') for i, code in enumerate(observed)}
    solver = z3.Solver(); solver.set(timeout=p['solver_ms'])
    solver.add(z3.Distinct(list(letters.values())))
    solver.add([z3.And(letter >= 0, letter < len(alphabet.symbols)) for letter in letters.values()])
    edges = []
    for i, word in enumerate(train_cipher):
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
        words = [decode(word) for word in train_cipher]
        assert len(set(recovered.values())) == len(recovered)
        assert all(a.accepts(word) and len(word) == len(cipher) for word, cipher in zip(words, train_cipher))
        row.update(verified=True, recovered_key=recovered, training_words=words)
        if arm == 'positive':
            held = [decode(word) for word in p['held_cipher']]
            row.update(training_exact=sum(w == t for w, t in zip(words, p['truth']['train'])),
                       held_words=held, held_exact=sum(w == t for w, t in zip(held, p['truth']['held'])),
                       held_members=sum(a.accepts(w) for w in held))
    elif status == z3.unknown: row['reason'] = solver.reason_unknown()
    timings['verification_seconds'] = perf_counter() - start
    row.update(timings=timings, worker_elapsed_seconds=perf_counter() - total)
    write_json(OUT / f'{arm}-result.json', row); checkpoint('complete')


def run():
    p = prepare(); rows = {}
    for arm in p['arms']:
        path = OUT / f'{arm}-result.json'
        print(arm, flush=True)
        if not path.exists():
            start = perf_counter()
            try:
                result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_layered_diversity', '--worker', arm],
                                        capture_output=True, text=True, timeout=p['worker_wall_seconds'])
                if result.returncode: raise RuntimeError(result.stderr[-2000:])
            except subprocess.TimeoutExpired:
                write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter() - start})
        rows[arm] = json.loads(path.read_text()); print(rows[arm], flush=True)
    write_json(OUT / 'report.json', {'prepared_sha256': digest(p), 'complete': True, 'arms': rows})


def validate():
    from collections import Counter
    p = prepare(); report = json.loads((OUT / 'report.json').read_text())
    assert report['complete'] and report['prepared_sha256'] == digest(p)
    positive, shuffled = p['arms']['positive'], p['arms']['shuffle']
    assert list(map(len, positive)) == list(map(len, shuffled))
    assert Counter(c for w in positive for c in w) == Counter(c for w in shuffled for c in w)
    a = compact.load_automaton(p['case']['automaton'])
    assert all(a.accepts(w) for w in p['truth']['train'] + p['truth']['held'])
    assert not set(p['truth']['train']) & set(p['truth']['held'])
    assert set(''.join(p['truth']['held'])) <= set(''.join(p['truth']['train']))
    assert positive == [[p['truth']['key'][c] for c in w] for w in p['truth']['train']]
    assert p['held_cipher'] == [[p['truth']['key'][c] for c in w] for w in p['truth']['held']]
    for arm, row in report['arms'].items():
        assert row == json.loads((OUT / f'{arm}-result.json').read_text())
        phases = json.loads((OUT / f'{arm}-phases.json').read_text())
        assert phases['prepared_sha256'] == digest(p)
        assert row['status'] in ('SAT', 'UNSAT', 'UNKNOWN', 'WALL_TIMEOUT')
        if arm == 'positive': assert row['status'] != 'UNSAT'
        if row['status'] != 'WALL_TIMEOUT':
            assert phases['phase'] == 'complete' and phases['timings'] == row['timings']
        if row['status'] == 'SAT':
            key = row['recovered_key']; decode = lambda w: ''.join(key[c] for c in w)
            words = [decode(w) for w in p['arms'][arm]]
            assert row['verified'] and len(set(key.values())) == len(key)
            assert words == row['training_words'] and all(a.accepts(w) for w in words)
            if arm == 'positive':
                held = [decode(w) for w in p['held_cipher']]
                assert row['training_exact'] == sum(w == t for w,t in zip(words,p['truth']['train']))
                assert held == row['held_words'] and row['held_exact'] == sum(w == t for w,t in zip(held,p['truth']['held']))
                assert row['held_members'] == sum(a.accepts(w) for w in held)
    write_json(OUT / 'validation.json', {'verified': True, 'arms': 2})
    print('Validated diverse shared-key paired controls')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', choices=['positive', 'shuffle']); args = parser.parse_args()
    if args.worker: worker(args.worker)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
