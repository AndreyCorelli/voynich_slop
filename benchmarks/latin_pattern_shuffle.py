"""One frozen length-eight replay with durable phase timings."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import z3
from benchmarks import latin_pattern_filter as baseline
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.language.word_patterns import equality_pattern, pattern_subsets
from voynich_smt.language.word_automaton import WordAutomaton
import random
from itertools import product
from benchmarks import latin_compact_membership as compact
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.layered_membership import layered_membership

OUT = Path('experiments/results/latin-pattern-shuffle')


def prepare():
    source = baseline.prepare()
    positive = source['arms']['positive']
    shuffled = pattern_preserving_shuffle(positive, 5004)
    assert shuffled != positive
    p = {**source, 'baseline_sha256': digest(source), 'reference_positive': positive,
         'arms': {'shuffle': shuffled}, 'shuffle_seed': 5004,
         'code_sha256': digest(Path(__file__).read_text()),
         'shuffle_code_sha256': digest(Path('src/voynich_smt/cipher/pattern_shuffle.py').read_text()),
         'scope': 'One harder randomized control preserving exact per-word equality patterns, per-word code counts and lengths. Same pattern-filter encoding, full inventory, budgets and key model. Reuses frozen positive input/reference; does not refit positive or guarantee randomized UNSAT.'}
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
    checkpoint('filtering'); start = perf_counter()
    metadata = json.loads((compact.OUT / 'prepared.json').read_text())['inventories']['upstream-default']['inventory']
    import hashlib
    assert hashlib.sha256(Path(metadata['path']).read_bytes()).hexdigest() == metadata['sha256']
    subsets = pattern_subsets(compact.inventory_lines(metadata['path']), [equality_pattern(w) for w in train_cipher])
    automata = {pattern: WordAutomaton.from_sorted(words) for pattern, words in subsets.items() if words}
    timings['filter_seconds'] = perf_counter() - start
    checkpoint('constructing'); start = perf_counter()
    observed = sorted({code for word in train_cipher for code in word})
    letters = {code: z3.Int(f'key_{i}') for i, code in enumerate(observed)}
    solver = z3.Solver(); solver.set(timeout=p['solver_ms'])
    solver.add(z3.Distinct(list(letters.values())))
    solver.add([z3.And(letter >= 0, letter < len(alphabet.symbols)) for letter in letters.values()])
    edges = []
    for i, word in enumerate(train_cipher):
        pattern = equality_pattern(word)
        if pattern in automata:
            formula, _, counts = layered_membership(automata[pattern], alphabet, [letters[c] for c in word], f'word_{i}')
        else: formula, counts = z3.BoolVal(False), []
        solver.add(formula); edges.append(counts)
    timings['construction_seconds'] = perf_counter() - start
    checkpoint('solving'); start = perf_counter(); status = solver.check()
    timings['solver_seconds'] = perf_counter() - start
    row = {'status': str(status).upper(), 'verified': False, 'layer_edges': edges, 'candidate_counts': [len(subsets[equality_pattern(w)]) for w in train_cipher]}
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
                result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_pattern_shuffle', '--worker', arm],
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
    positive, shuffled = p['reference_positive'], p['arms']['shuffle']
    assert shuffled == pattern_preserving_shuffle(positive, p['shuffle_seed'])
    assert all(equality_pattern(a) == equality_pattern(b) and Counter(a) == Counter(b) for a,b in zip(positive, shuffled))
    assert list(map(len, positive)) == list(map(len, shuffled))
    assert Counter(c for w in positive for c in w) == Counter(c for w in shuffled for c in w)
    a = compact.load_automaton(p['case']['automaton'])
    assert all(a.accepts(w) for w in p['truth']['train'] + p['truth']['held'])
    assert not set(p['truth']['train']) & set(p['truth']['held'])
    assert set(''.join(p['truth']['held'])) <= set(''.join(p['truth']['train']))
    assert positive == [[p['truth']['key'][c] for c in w] for w in p['truth']['train']]
    assert p['held_cipher'] == [[p['truth']['key'][c] for c in w] for w in p['truth']['held']]
    metadata = compact.prepare()['inventories']['upstream-default']['inventory']
    subsets = pattern_subsets(compact.inventory_lines(metadata['path']),
                              [equality_pattern(w) for words in p['arms'].values() for w in words])
    for arm, row in report['arms'].items():
        assert row == json.loads((OUT / f'{arm}-result.json').read_text())
        phases = json.loads((OUT / f'{arm}-phases.json').read_text())
        assert phases['prepared_sha256'] == digest(p)
        assert row['status'] in ('SAT', 'UNSAT', 'UNKNOWN', 'WALL_TIMEOUT')
        if arm == 'positive': assert row['status'] != 'UNSAT'
        if row['status'] != 'WALL_TIMEOUT':
            assert row['candidate_counts'] == [len(subsets[equality_pattern(w)]) for w in p['arms'][arm]]
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
    write_json(OUT / 'validation.json', {'verified': True, 'arms': 1})
    print('Validated pattern-preserving shuffled control')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', choices=['positive', 'shuffle']); args = parser.parse_args()
    if args.worker: worker(args.worker)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
