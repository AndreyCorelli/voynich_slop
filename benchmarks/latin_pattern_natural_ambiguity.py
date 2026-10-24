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
from benchmarks import latin_pattern_natural_replication as baseline
from benchmarks import latin_morphology_coverage as morphology
import z3
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.language.word_automaton import WordAutomaton
from voynich_smt.solver.layered_membership import layered_membership
from benchmarks import latin_compact_membership as compact
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.word_patterns import equality_pattern, pattern_subsets

OUT = Path('experiments/results/latin-pattern-natural-ambiguity')
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


def select_passages(records, start, alphabet, count=3):
    selected = []
    while len(selected) < count:
        for candidate in range(start, len(records) - 29):
            block = records[candidate:candidate + 30]
            words = [morphology.canonical(''.join(record['tokens'])) for record in block]
            if any(record.get('excluded_reason') is not None or not word or not set(word) <= alphabet
                   for record, word in zip(block, words)): continue
            train, held = words[:24], words[24:]
            if len(set(held) - set(train)) < 3 or not set(''.join(held)) <= set(''.join(train)): continue
            selected.append({'record_start': candidate, 'record_end_exclusive': candidate + 30,
                             'source_records': block, 'train': train, 'held': held})
            start = candidate + 30; break
        else: raise ValueError('No structurally eligible contiguous passage; no coverage selection')
    return selected


def prepare():
    source = baseline.prepare(); report = json.loads((baseline.OUT / 'report.json').read_text())
    assert report['complete'] and report['prepared_sha256'] == digest(source)
    fixtures = []
    for old in source['fixtures']:
        first = report['fixtures'][old['id']]['positive']
        if first['status'] != 'SAT': continue
        fixture = {**old, 'arms': {'positive': old['arms']['positive']},
                   'excluded_key': first['recovered_key'], 'first_result_sha256': digest(first)}
        fixtures.append(fixture)
    p = {'baseline_sha256': digest(source), 'baseline_report_sha256': digest(report),
         'code_sha256': digest(Path(__file__).read_text()), 'fixtures': fixtures,
         'scope': 'Second-key existence on each admitted natural positive, excluding exactly the first observed-code key. Same constraints/budgets. Alternate score diagnostic only, no replacement of first-key scores or truth constraints.'}
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
    subsets = pattern_subsets(compact.inventory_lines(metadata['path']), [equality_pattern(w) for w in train_cipher])
    automata = {pattern: WordAutomaton.from_sorted(words) for pattern, words in subsets.items() if words}
    timings['filter_seconds'] = perf_counter() - start
    checkpoint('constructing'); start = perf_counter()
    observed = sorted({code for word in train_cipher for code in word})
    letters = {code: z3.Int(f'key_{i}') for i, code in enumerate(observed)}
    solver = z3.Solver(); solver.set(timeout=p['solver_ms'])
    solver.add(z3.Distinct(list(letters.values())))
    solver.add([z3.And(letter >= 0, letter < len(alphabet.symbols)) for letter in letters.values()])
    solver.add(z3.Or([letters[code] != alphabet.index(letter) for code,letter in p['excluded_key'].items()]))
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
    for i, fixture in enumerate(p['fixtures']):
        folder = OUT / fixture['id']; write_json(folder / 'prepared.json', fixture)
        rows[fixture['id']] = {}
        for arm in fixture['arms']:
            path = folder / f'{arm}-result.json'
            print(fixture['id'], arm, flush=True)
            if not path.exists():
                start = perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_pattern_natural_ambiguity', '--worker', str(i), '--arm', arm],
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
    source = compact.prepare()
    for fixture in p['fixtures']:
        a = compact.load_automaton(fixture['case']['automaton'])
        metadata = source['inventories'][fixture['case']['mode']]['inventory']
        subsets = pattern_subsets(compact.inventory_lines(metadata['path']), [equality_pattern(w) for words in fixture['arms'].values() for w in words])
        folder = OUT / fixture['id']; assert fixture == json.loads((folder / 'prepared.json').read_text())
        train, held, key = (fixture['truth'][name] for name in ('train', 'held', 'key'))
        positive = fixture['arms']['positive']
        assert all(a.accepts(w) for w in train)
        assert fixture['novel_held'] == [w not in train for w in held]
        assert set(''.join(held)) <= set(''.join(train))
        assert positive == [[key[c] for c in w] for w in train]
        assert fixture['held_cipher'] == [[key[c] for c in w] for w in held]

        for arm, row in report['fixtures'][fixture['id']].items():
            assert row == json.loads((folder / f'{arm}-result.json').read_text())
            phase = json.loads((folder / f'{arm}-phases.json').read_text()); assert phase['prepared_sha256'] == digest(fixture)
            assert row['status'] in ('SAT','UNSAT','UNKNOWN','WALL_TIMEOUT')

            if row['status'] != 'WALL_TIMEOUT':
                assert phase['phase'] == 'complete' and phase['timings'] == row['timings']
                assert row['candidate_counts'] == [len(subsets[equality_pattern(w)]) for w in fixture['arms'][arm]]
            if row['status'] == 'SAT':
                recovered = row['recovered_key']; assert recovered != fixture['excluded_key']; decode = lambda w: ''.join(recovered[c] for c in w)
                words = [decode(w) for w in fixture['arms'][arm]]
                assert row['verified'] and len(set(recovered.values())) == len(recovered)
                assert words == row['training_words'] and all(a.accepts(w) for w in words)
                if arm == 'positive':
                    predictions = [decode(w) for w in fixture['held_cipher']]
                    assert predictions == row['held_words']
                    assert row['training_exact'] == sum(x == y for x,y in zip(words,train))
                    assert row['held_exact'] == sum(x == y for x,y in zip(predictions,held))
                    assert row['held_members'] == sum(a.accepts(w) for w in predictions)
    write_json(OUT / 'validation.json', {'verified': True, 'fixtures': len(p['fixtures']), 'arms': len(p['fixtures'])})
    print('Validated natural passage alternative-key queries')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', type=int); parser.add_argument('--arm', choices=['positive','shuffle'])
    args = parser.parse_args()
    if args.worker is not None: worker(args.worker, args.arm)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
