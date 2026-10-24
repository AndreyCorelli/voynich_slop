"""Seven fresh natural Latin cyclic/random training-choice comparisons."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_natural_context as context
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json

OUT = Path('experiments/results/latin-h2-natural-random')
TASKS = context.TASKS


def random_encrypt(words, key, seed):
    """Independent uniform choices; no balancing or per-letter cycle."""
    rng = random.Random(seed)
    return [[key[letter][rng.randrange(2)] for letter in word] for word in words]


def protocol():
    source = context.prior.prepare()
    raw = json.loads(Path(source['source_path']).read_text())
    compact = context.prior.baseline.compact
    report = json.loads((compact.OUT/'report.json').read_text())
    inventory_source = json.loads((compact.OUT/'prepared.json').read_text())
    mode = 'through-medieval-rare'
    case = {**report['modes'][mode], 'mode': mode, 'kind': 'natural-h2-random'}
    start = max(block['record_end_exclusive'] for block in source['passages'])
    selected = context.prior.passages.select_passages(raw['records'], start, set(case['alphabet']['symbols']), count=7)
    automata = {m: compact.load_automaton(row['automaton']) for m, row in report['modes'].items()}
    jobs = []
    for index, block in enumerate(selected):
        train, held = block['train'], block['held']
        codes = [''.join(x) for x in product('qrstuvwx', repeat=2)]
        random.Random(11201+index).shuffle(codes)
        key = {letter: codes[2*j:2*j+2] for j, letter in enumerate(case['alphabet']['symbols'])}
        cyclic, _ = context.prior.baseline.encrypt(train, [], key)
        random_train = random_encrypt(train, key, 11401+index)
        # Shared independent random holdout choices isolate training selection.
        held_cipher = random_encrypt(held, key, 11501+index)
        coverage = {m: {'missing_training': [w for w in train if not a.accepts(w)],
                        'missing_held': [w for w in held if not a.accepts(w)]} for m, a in automata.items()}
        for selection, positive in (('cyclic', cyclic), ('iid-random', random_train)):
            seen = {c for word in positive for c in word}
            mask = [all(c in seen for c in word) for word in held_cipher]
            admitted = not coverage[mode]['missing_training']
            fixture = {'id': f'passage-{index+1}', 'case': case,
                'inventory': inventory_source['inventories'][mode]['inventory'],
                'solver_ms': 30000, 'worker_wall_seconds': 60, 'max_homophones': 2,
                'arms': {'positive': positive, 'shuffle': pattern_preserving_shuffle(positive, 11301+index)},
                'held_cipher': [w for w, covered in zip(held_cipher, mask) if covered],
                'truth': {'train': train, 'held': [w for w, covered in zip(held, mask) if covered], 'key': key},
                'key_seed': 11201+index, 'shuffle_seed': 11301+index}
            jobs.append({'job': f'passage-{index+1}-{selection}', 'pair': index+1, 'selection': selection,
                'training_length': 48, 'record_start': block['record_start'], 'training_end_exclusive': block['record_start']+48,
                'structural_failures': [], 'coverage': coverage, 'admitted': admitted,
                'full_held': held, 'full_held_cipher': held_cipher, 'covered_mask': mask,
                'observed_codes': sorted(seen), 'reuse': None, 'fixture': fixture,
                'training_choice_seed': 11401+index if selection == 'iid-random' else None,
                'held_choice_seed': 11501+index})
    paths = [Path(__file__), Path(context.__file__), Path(context.prior.__file__), Path(context.prior.baseline.__file__),
             Path(context.prior.passages.__file__), Path(context.prior.baseline.engine.__file__), Path(context.prior.baseline.encoding.__file__)]
    paths += list(Path('src/voynich_smt/solver').glob('*.py'))
    paths += [Path('src/voynich_smt/language/homophone_patterns.py'), Path('src/voynich_smt/cipher/pattern_shuffle.py')]
    return {'prior_sha256': digest(source), 'source_sha256': digest(raw), 'passages': selected, 'jobs': jobs,
        'code_sha256': {str(path): digest(path.read_text()) for path in paths},
        'scope': 'Seven fresh 48+6 contiguous Caesar passages selected structurally after prior material, before dictionary audits and fits. Paired cyclic versus independent uniform random training choices; same key/plaintext/full inventory and independently random shared held ciphertext. No forced balance, duplicate words or both-code coverage. Missing training forms gate without replacement; individual unseen-code holdouts unevaluated. Free H<=2/public boundaries/two-glyph codes; first key, 30s Z3/60s worker per task. No reused results or truth additions.'}


def prepare():
    p = protocol(); path = OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p, 'Frozen protocol changed'
    else: write_json(path, p)
    return p


def worker(job, task):
    folder = OUT/job
    if task == 'ambiguity': context.prior.baseline.ambiguity(folder)
    else: context.prior.baseline.encoding.configure(folder, 'dag'); context.prior.baseline.engine.fit(task)


def run():
    p = prepare()
    print('Frozen seven fresh pairs;', sum(job['admitted'] for job in p['jobs']), 'admitted conditions', flush=True)
    for job in p['jobs']:
        if not job['admitted']: print(job['job'], 'NOT_ADMITTED', flush=True); continue
        fixture = job['fixture']; folder = OUT/job['job']; write_json(folder/'prepared.json', fixture)
        for task in TASKS:
            path = folder/f'{task}-result.json'; print(job['job'], task, flush=True)
            if not path.exists():
                start = perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_h2_natural_random', '--worker', job['job'], '--task', task], capture_output=True, text=True, timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter()-start, 'fixture_sha256': digest(fixture)})
            row = json.loads(path.read_text()); print(row['status'], row.get('training_exact'), row.get('held_exact'), flush=True)
    validate()


def validate():
    p = prepare(); old = context.OUT, context.prepare
    try:
        context.OUT = OUT; context.prepare = lambda: p; context.validate()
    finally: context.OUT, context.prepare = old
    report = json.loads((OUT/'report.json').read_text()); comparisons = []
    for cyclic, stochastic in zip(p['jobs'][::2], p['jobs'][1::2]):
        assert cyclic['pair'] == stochastic['pair']
        a, b = cyclic['fixture'], stochastic['fixture']
        assert a['truth']['train'] == b['truth']['train'] and a['truth']['key'] == b['truth']['key']
        assert a['inventory'] == b['inventory'] and a['case'] == b['case']
        assert cyclic['full_held'] == stochastic['full_held'] and cyclic['full_held_cipher'] == stochastic['full_held_cipher']
        assert cyclic['coverage'] == stochastic['coverage']
        for job in (cyclic, stochastic):
            f = job['fixture']; words = f['truth']['train']; key = f['truth']['key']
            generated = context.prior.baseline.encrypt(words, [], key)[0] if job['selection'] == 'cyclic' else random_encrypt(words, key, job['training_choice_seed'])
            assert generated == f['arms']['positive']
            assert random_encrypt(job['full_held'], key, job['held_choice_seed']) == job['full_held_cipher']
            assert len({c for codes in key.values() for c in codes}) == 2*len(key)
        comparisons.append({'pair': cyclic['pair'], 'record_start': cyclic['record_start'], 'conditions': {
            job['selection']: {**next(row for row in report['conditions'] if row['job'] == job['job']),
                               'observed_codes': len(job['observed_codes'])} for job in (cyclic, stochastic)}})
    write_json(OUT/'comparison.json', {'prepared_sha256': digest(p), 'pairs': comparisons})
    write_json(OUT/'validation.json', {'verified': True, 'pairs': 7, 'conditions': 14,
        'admitted': sum(job['admitted'] for job in p['jobs']), 'new_records': 3*sum(job['admitted'] for job in p['jobs']), 'reused_records': 0})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true'); parser.add_argument('--worker'); parser.add_argument('--task', choices=TASKS); args = parser.parse_args()
    if args.worker: worker(args.worker, args.task)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
