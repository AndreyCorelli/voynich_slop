"""Frozen independent synthetic fixture replication of exact-pattern recovery."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter
from itertools import product
from benchmarks import latin_pattern_replication as baseline
from voynich_smt.language.homophone_patterns import homophone_subsets
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.language.word_automaton import WordAutomaton
from voynich_smt.solver.layered_membership import layered_membership
import z3
from benchmarks import latin_compact_membership as compact
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.word_patterns import equality_pattern, pattern_subsets

OUT = Path('experiments/results/latin-h2-public')
SEEDS = (5101, 5102, 5103)


def select_fixture(eligible, seed):
    pool = sorted(random.Random(seed).sample(eligible, 512))
    train = []; covered = set()
    for _ in range(12):
        word = min(pool, key=lambda w: (-len(set(w) - covered), w))
        train.append(word); covered.update(word); pool.remove(word)
    held = [word for word in pool if set(word) <= covered][:3]
    assert len(held) == 3
    return train, held


def prepare():
    source = baseline.prepare(); fixtures = []
    for index, old in enumerate(source['fixtures']):
        train = old['truth']['train'] * 2; held = old['truth']['held']
        codes = [''.join(pair) for pair in product('qrstuvwx', repeat=2)]
        random.Random(6001 + index).shuffle(codes)
        key = {letter: codes[2*i:2*i+2] for i,letter in enumerate(old['case']['alphabet']['symbols'])}
        counters = Counter()
        def encrypt(word):
            out = []
            for letter in word:
                out.append(key[letter][counters[letter] % 2]); counters[letter] += 1
            return out
        positive = [encrypt(w) for w in train]; held_cipher = [encrypt(w) for w in held]
        observed = {code for w in positive for code in w}
        assert all(code in observed for w in held_cipher for code in w)
        assert all(set(key[c]) <= observed for c in set(''.join(train)))
        shuffle = pattern_preserving_shuffle(positive, 6101 + index); assert shuffle != positive
        fixtures.append({'id': old['id'], 'case': {**old['case'], 'mode': 'upstream-default'},
                         'solver_ms': 30000, 'worker_wall_seconds': 60, 'max_homophones': 2,
                         'arms': {'positive': positive, 'shuffle': shuffle}, 'held_cipher': held_cipher,
                         'truth': {'train': train, 'held': held, 'key': key},
                         'key_seed': 6001+index, 'shuffle_seed': 6101+index,
                         'scope': 'Two copies of twelve frozen synthetic word types exercise both homophones; three novel code-covered holdouts. Public fixed-two boundaries/word lengths. Generating per-letter alternation not constrained in fit; free choice, H<=2.'})
    paths = [Path(__file__), Path('src/voynich_smt/language/homophone_patterns.py'),
             Path('src/voynich_smt/solver/layered_membership.py'), Path('src/voynich_smt/cipher/pattern_shuffle.py')]
    p = {'baseline_sha256': digest(source), 'code_sha256': {str(path): digest(path.read_text()) for path in paths},
         'fixtures': fixtures, 'scope': 'Iteration 1: three synthetic H2 positives and matched controls, frozen before fits. Full default inventory/alphabet. Sound local weak-pattern filtering plus global two-code capacity per letter. No Distinct plaintext assignments, no H1 equality filter, no truth/held constraints. First-key scoring only.'}
    path = OUT / 'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p
    else: write_json(path, p)
    return p


def worker(index, arm):
    global OUT
    root = OUT; p = json.loads((root / 'prepared.json').read_text()); fixture = p['fixtures'][index]
    OUT = root / fixture['id']; fit(arm)


def fit(arm):
    p = json.loads((OUT / 'prepared.json').read_text()); case = p['case']; timings = {}; train_cipher = p['arms'][arm]
    total = perf_counter()
    def checkpoint(phase):
        write_json(OUT / f'{arm}-phases.json', {'prepared_sha256': digest(p), 'phase': phase,
                                        'timings': timings, 'worker_elapsed_seconds': perf_counter() - total})
    checkpoint('loading'); start = perf_counter()
    a = compact.load_automaton(case['automaton']); alphabet = Alphabet(tuple(case['alphabet']['symbols']))
    timings['load_seconds'] = perf_counter() - start
    checkpoint('filtering'); start = perf_counter()
    metadata = json.loads((compact.OUT / 'prepared.json').read_text())['inventories'][case['mode']]['inventory']
    import hashlib
    assert hashlib.sha256(Path(metadata['path']).read_bytes()).hexdigest() == metadata['sha256']
    subsets = homophone_subsets(compact.inventory_lines(metadata['path']), [equality_pattern(w) for w in train_cipher])
    automata = {pattern: WordAutomaton.from_sorted(words) for pattern, words in subsets.items() if words}
    timings['filter_seconds'] = perf_counter() - start
    checkpoint('constructing'); start = perf_counter()
    observed = sorted({code for word in train_cipher for code in word})
    letters = {code: z3.Int(f'key_{i}') for i, code in enumerate(observed)}
    solver = z3.Solver(); solver.set(timeout=p['solver_ms'])
    solver.add([z3.PbLe([(letter == value, 1) for letter in letters.values()], p['max_homophones']) for value in range(len(alphabet.symbols))])
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
        assert max(Counter(recovered.values()).values()) <= p['max_homophones']
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
    for i, fixture in enumerate(p['fixtures']):
        folder = OUT / fixture['id']; write_json(folder / 'prepared.json', fixture)
        rows[fixture['id']] = {}
        for arm in fixture['arms']:
            path = folder / f'{arm}-result.json'
            print(fixture['id'], arm, flush=True)
            if not path.exists():
                start = perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_h2_public', '--worker', str(i), '--arm', arm],
                                            capture_output=True, text=True, timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-2000:])
                except subprocess.TimeoutExpired:
                    write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter() - start})
            row = json.loads(path.read_text()); rows[fixture['id']][arm] = row
            print(row['status'], row.get('timings'), 'held_exact=', row.get('held_exact'), flush=True)
        write_json(OUT / 'report.json', {'prepared_sha256': digest(p), 'complete': False, 'fixtures': rows})
    write_json(OUT / 'report.json', {'prepared_sha256': digest(p), 'complete': True, 'fixtures': rows})


def validate():
    p = prepare(); report = json.loads((OUT / 'report.json').read_text())
    assert report['complete'] and report['prepared_sha256'] == digest(p)
    metadata = compact.prepare()['inventories']['upstream-default']['inventory']
    patterns = [equality_pattern(w) for f in p['fixtures'] for words in f['arms'].values() for w in words]
    subsets = homophone_subsets(compact.inventory_lines(metadata['path']), patterns)
    a = compact.load_automaton(p['fixtures'][0]['case']['automaton'])
    for fixture in p['fixtures']:
        folder = OUT / fixture['id']; assert fixture == json.loads((folder / 'prepared.json').read_text())
        train, held, key = (fixture['truth'][name] for name in ('train', 'held', 'key'))
        positive, shuffle = (fixture['arms'][name] for name in ('positive', 'shuffle'))
        assert all(a.accepts(w) for w in train + held) and not set(train) & set(held)
        assert set(''.join(held)) <= set(''.join(train))
        assert all(all(code in key[c] for c,code in zip(w,cipher)) for w,cipher in zip(train,positive))
        assert all(all(code in key[c] for c,code in zip(w,cipher)) for w,cipher in zip(held,fixture['held_cipher']))
        assert len({code for codes in key.values() for code in codes}) == 2*len(key)
        assert all(code in {c for w in positive for c in w} for w in fixture['held_cipher'] for code in w)
        assert shuffle == pattern_preserving_shuffle(positive, fixture['shuffle_seed'])
        assert all(Counter(x) == Counter(y) and equality_pattern(x) == equality_pattern(y) for x,y in zip(positive, shuffle))
        for arm, row in report['fixtures'][fixture['id']].items():
            assert row == json.loads((folder / f'{arm}-result.json').read_text())
            phase = json.loads((folder / f'{arm}-phases.json').read_text()); assert phase['prepared_sha256'] == digest(fixture)
            assert row['status'] in ('SAT','UNSAT','UNKNOWN','WALL_TIMEOUT')
            if arm == 'positive': assert row['status'] != 'UNSAT'
            if row['status'] != 'WALL_TIMEOUT':
                assert phase['phase'] == 'complete' and phase['timings'] == row['timings']
                assert row['candidate_counts'] == [len(subsets[equality_pattern(w)]) for w in fixture['arms'][arm]]
            if row['status'] == 'SAT':
                recovered = row['recovered_key']; decode = lambda w: ''.join(recovered[c] for c in w)
                words = [decode(w) for w in fixture['arms'][arm]]
                assert row['verified'] and max(Counter(recovered.values()).values()) <= fixture['max_homophones']
                assert words == row['training_words'] and all(a.accepts(w) for w in words)
                if arm == 'positive':
                    predictions = [decode(w) for w in fixture['held_cipher']]
                    assert predictions == row['held_words']
                    assert row['training_exact'] == sum(x == y for x,y in zip(words,train))
                    assert row['held_exact'] == sum(x == y for x,y in zip(predictions,held))
                    assert row['held_members'] == sum(a.accepts(w) for w in predictions)
    write_json(OUT / 'validation.json', {'verified': True, 'fixtures': 3, 'arms': 6})
    print('Validated public-boundary H2 controls')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', type=int); parser.add_argument('--arm', choices=['positive','shuffle'])
    args = parser.parse_args()
    if args.worker is not None: worker(args.worker, args.arm)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
