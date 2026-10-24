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
from benchmarks import latin_pattern_filter as engine
from benchmarks import latin_compact_membership as compact
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.word_patterns import equality_pattern, pattern_subsets

OUT = Path('experiments/results/latin-pattern-replication')
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
    source = engine.prepare(); metadata = compact.prepare()['inventories']['upstream-default']['inventory']
    eligible = [w for w in compact.inventory_lines(metadata['path']) if 3 <= len(w) <= 6]
    fixtures = []
    for i, seed in enumerate(SEEDS):
        train, held = select_fixture(eligible, seed)
        codes = [''.join(pair) for pair in product('uvwxyz', repeat=2)]
        random.Random(5201 + i).shuffle(codes)
        key = dict(zip(source['case']['alphabet']['symbols'], codes))
        encrypt = lambda word: [key[c] for c in word]
        positive = [encrypt(w) for w in train]; shuffle = pattern_preserving_shuffle(positive, 5301 + i)
        assert shuffle != positive
        fixtures.append({'id': f'seed-{seed}', 'case': source['case'],
                         'solver_ms': 30000, 'worker_wall_seconds': 60,
                         'arms': {'positive': positive, 'shuffle': shuffle},
                         'held_cipher': [encrypt(w) for w in held],
                         'truth': {'train': train, 'held': held, 'key': key},
                         'selection_seed': seed, 'key_seed': 5201 + i, 'shuffle_seed': 5301 + i,
                         'coverage': len(set(''.join(train)))})
    paths = [Path(__file__), Path(engine.__file__), Path('src/voynich_smt/language/word_patterns.py'),
             Path('src/voynich_smt/solver/layered_membership.py'), Path('src/voynich_smt/cipher/pattern_shuffle.py')]
    p = {'baseline_sha256': digest(source), 'code_sha256': {str(path): digest(path.read_text()) for path in paths},
         'eligible_count': len(eligible), 'fixtures': fixtures,
         'scope': 'Three independently seeded 512-word samples from complete length-3..6 inventory; twelve greedy coverage training forms and three novel covered holdouts per fixture. New keys and pattern-preserving shuffles; all frozen before any fit. Same budgets, model and first-key scoring. Generated forms, not natural prose. All cases reported.'}
    path = OUT / 'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p, 'Frozen protocol changed'
    else: write_json(path, p)
    return p


def worker(index, arm):
    p = json.loads((OUT / 'prepared.json').read_text()); fixture = p['fixtures'][index]
    engine.OUT = OUT / fixture['id']; engine.worker(arm)


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
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_pattern_replication', '--worker', str(i), '--arm', arm],
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
    subsets = pattern_subsets(compact.inventory_lines(metadata['path']), patterns)
    a = compact.load_automaton(p['fixtures'][0]['case']['automaton'])
    for fixture in p['fixtures']:
        folder = OUT / fixture['id']; assert fixture == json.loads((folder / 'prepared.json').read_text())
        train, held, key = (fixture['truth'][name] for name in ('train', 'held', 'key'))
        positive, shuffle = (fixture['arms'][name] for name in ('positive', 'shuffle'))
        assert all(a.accepts(w) for w in train + held) and not set(train) & set(held)
        assert set(''.join(held)) <= set(''.join(train))
        assert positive == [[key[c] for c in w] for w in train]
        assert fixture['held_cipher'] == [[key[c] for c in w] for w in held]
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
                assert row['verified'] and len(set(recovered.values())) == len(recovered)
                assert words == row['training_words'] and all(a.accepts(w) for w in words)
                if arm == 'positive':
                    predictions = [decode(w) for w in fixture['held_cipher']]
                    assert predictions == row['held_words']
                    assert row['training_exact'] == sum(x == y for x,y in zip(words,train))
                    assert row['held_exact'] == sum(x == y for x,y in zip(predictions,held))
                    assert row['held_members'] == sum(a.accepts(w) for w in predictions)
    write_json(OUT / 'validation.json', {'verified': True, 'fixtures': 3, 'arms': 6})
    print('Validated three independent paired fixtures')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', type=int); parser.add_argument('--arm', choices=['positive','shuffle'])
    args = parser.parse_args()
    if args.worker is not None: worker(args.worker, args.arm)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
