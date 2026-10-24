"""Seventh compressed-membership iteration selected without holdout scores."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_compressed as comparison
from benchmarks import latin_h2_semijoin_replication as independent
from benchmarks import latin_h2_pool as engine
from voynich_smt.data.corpus import digest, write_json

OUT = Path('experiments/results/latin-h2-compressed-replication')


def choose_mode(trials):
    eligible = [mode for mode, rows in trials.items() if rows['small']['status'] == 'SAT']
    if not eligible: raise ValueError('No encoding passes the resolved positive regression')
    resolved = [mode for mode in eligible if trials[mode]['large']['status'] == 'SAT']
    if resolved:
        return min(resolved, key=lambda mode: (trials[mode]['large']['elapsed'], mode))
    finished = [mode for mode in eligible if 'construction' in trials[mode]['large']]
    if not finished: raise ValueError('No completed construction available for selection')
    return min(finished, key=lambda mode: (trials[mode]['large']['construction'], mode))


def prepare():
    source = comparison.prepare()
    assert json.loads((comparison.OUT / 'validation.json').read_text())['verified']
    trials = {}; hashes = {}
    for rung in source['rungs']:
        report_path = comparison.OUT / rung['job'] / 'report.json'
        report = json.loads(report_path.read_text())
        assert report['complete'] and report['prepared_sha256'] == digest(rung)
        row = report['fixtures'][rung['fixtures'][0]['id']]['positive']
        stats = {'status': row['status'], 'elapsed': row.get('worker_elapsed_seconds', row.get('wall_seconds'))}
        if 'timings' in row: stats['construction'] = row['timings']['construction_seconds']
        trials.setdefault(rung['mode'], {})['small' if rung['size'] == 16384 else 'large'] = stats
        hashes[str(report_path)] = digest(report)
    mode = choose_mode(trials)
    replication = independent.prepare(); fixture = replication['rungs'][0]['fixtures'][0]
    assert fixture['id'].endswith('5102') and fixture['inventory']['word_count'] == 16384
    rung = {'mode': mode, 'fixtures': [fixture]}
    p = {'comparison_sha256': digest(source), 'independent_sha256': digest(replication), 'report_sha256': hashes,
         'selection': {'mode': mode, 'trials': trials, 'rule': 'Require SAT on 16384 positive. Prefer SAT on 32768 positive with least total worker elapsed; otherwise least construction time on completed 32768 positive. Lexical mode tie break. Never inspect holdout accuracy for selection.'},
         'rung': rung, 'code_sha256': {str(Path(__file__)): digest(Path(__file__).read_text())},
         'scope': 'Replay the previously fixed independent seed-5102 16384-form fixture with selected representation. Same pruning/budgets/first-key scoring; representation regression, not a new blind holdout.'}
    path = OUT / 'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p
    else: write_json(path, p)
    return p


def worker(arm):
    p = json.loads((OUT / 'prepared.json').read_text()); fixture = p['rung']['fixtures'][0]
    comparison.configure(OUT / fixture['id'], p['rung']['mode']); engine.fit(arm)


def run():
    p = prepare(); rung = p['rung']; fixture = rung['fixtures'][0]
    folder = OUT / fixture['id']; write_json(folder / 'prepared.json', fixture)
    rows = {}
    for arm in fixture['arms']:
        path = folder / f'{arm}-result.json'
        print('Selected', rung['mode'], fixture['id'], arm, flush=True)
        if not path.exists():
            start = perf_counter()
            try:
                result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_h2_compressed_replication', '--worker', arm], capture_output=True, text=True, timeout=fixture['worker_wall_seconds'])
                if result.returncode: raise RuntimeError(result.stderr[-3000:])
            except subprocess.TimeoutExpired:
                write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter()-start})
        rows[arm] = json.loads(path.read_text()); print(rows[arm]['status'], rows[arm].get('timings'), 'held=', rows[arm].get('held_exact'), flush=True)
    write_json(OUT / 'report.json', {'prepared_sha256': digest(rung), 'complete': True, 'fixtures': {fixture['id']: rows}})
    validate()


def validate():
    p = prepare(); rung = p['rung']
    old = engine.OUT, engine.prepare, engine.propagate_candidates, engine.candidate_membership
    try:
        comparison.configure(OUT, rung['mode']); engine.prepare = lambda: rung
        engine.validate()
    finally:
        engine.OUT, engine.prepare, engine.propagate_candidates, engine.candidate_membership = old


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker', choices=['positive','shuffle'])
    args = parser.parse_args()
    if args.worker: worker(args.worker)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
