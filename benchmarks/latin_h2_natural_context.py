"""Seven matched 48/96-word natural H2 context comparisons with partial holdouts."""
import argparse
from collections import Counter
import json
from itertools import product
from pathlib import Path
import random
import shutil
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_natural as prior
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json

OUT = Path('experiments/results/latin-h2-natural-context')
TASKS = ('positive', 'shuffle', 'ambiguity')


def prepend_cipher(prefix, train, held, key):
    """Align the preceding cycle so the existing train/held ciphertext stays fixed."""
    counts = Counter(''.join(prefix))
    counters = Counter({letter: -count for letter, count in counts.items()})
    def encode(word):
        result = []
        for letter in word:
            result.append(key[letter][counters[letter] % 2])
            counters[letter] += 1
        return result
    before = [encode(word) for word in prefix]
    assert all(counters[letter] == 0 for letter in key)
    positive = [encode(word) for word in train]
    held_cipher = [encode(word) for word in held]
    return before + positive, held_cipher


def evaluate_holdouts(key, cipher, truth):
    """Report unseen codes separately, never guess a missing key entry."""
    words = []
    for codes, target in zip(cipher, truth, strict=True):
        missing = sorted(set(codes) - set(key))
        if missing:
            words.append({'status': 'UNSEEN_CODE', 'missing_codes': missing})
        else:
            decoded = ''.join(key[code] for code in codes)
            words.append({'status': 'DECODED', 'word': decoded, 'exact': decoded == target})
    return {'words': words, 'covered': sum(w['status'] == 'DECODED' for w in words),
            'unseen': sum(w['status'] == 'UNSEEN_CODE' for w in words),
            'exact_covered': sum(w.get('exact', False) for w in words)}


def protocol():
    source = prior.prepare()
    raw = json.loads(Path(source['source_path']).read_text())
    report = json.loads((prior.baseline.compact.OUT/'report.json').read_text())
    compact = json.loads((prior.baseline.compact.OUT/'prepared.json').read_text())
    mode = 'through-medieval-rare'; case = {**report['modes'][mode], 'mode': mode, 'kind': 'natural-h2'}
    automata = {m: prior.baseline.compact.load_automaton(row['automaton']) for m, row in report['modes'].items()}
    jobs = []
    for index, block in enumerate(source['passages']):
        train, held = block['train'], block['held']
        start = block['record_start']
        prefix_records = raw['records'][start-48:start]
        assert len(prefix_records) == 48
        prefix = [prior.passages.morphology.canonical(''.join(r['tokens'])) for r in prefix_records]
        codes = [''.join(x) for x in product('qrstuvwx', repeat=2)]
        random.Random(10201+index).shuffle(codes)
        key = {letter: codes[2*j:2*j+2] for j, letter in enumerate(case['alphabet']['symbols'])}
        original, held_cipher = prior.baseline.encrypt(train, held, key)
        structural = [i for i, (r, word) in enumerate(zip(prefix_records, prefix))
                      if r.get('excluded_reason') is not None or not word or not set(word) <= set(case['alphabet']['symbols'])]
        for length in (48, 96):
            words = train if length == 48 else prefix+train
            invalid = [] if length == 48 else structural
            if invalid:
                positive = None
            else:
                positive, unchanged_held = prepend_cipher([] if length == 48 else prefix, train, held, key)
                assert unchanged_held == held_cipher
                assert positive[-48:] == original
            coverage = {m: {'missing_training': [w for w in words if not a.accepts(w)],
                            'missing_held': [w for w in held if not a.accepts(w)]} for m, a in automata.items()}
            seen = {c for word in positive for c in word} if positive is not None else set()
            mask = [all(c in seen for c in word) for word in held_cipher] if positive is not None else None
            admitted = not invalid and not coverage[mode]['missing_training']
            job = {'job': f"passage-{index+1}-words-{length}", 'pair': index+1, 'training_length': length,
                   'record_start': start if length == 48 else start-48, 'training_end_exclusive': start+48,
                   'prefix_records': [] if length == 48 else prefix_records,
                   'structural_failures': invalid, 'coverage': coverage, 'admitted': admitted,
                   'full_held': held, 'full_held_cipher': held_cipher, 'covered_mask': mask,
                   'observed_codes': sorted(seen), 'reuse': None, 'fixture': None}
            if admitted:
                fixture = {'id': f'passage-{index+1}', 'case': case,
                    'inventory': compact['inventories'][mode]['inventory'], 'solver_ms': 30000,
                    'worker_wall_seconds': 60, 'max_homophones': 2,
                    'arms': {'positive': positive, 'shuffle': pattern_preserving_shuffle(positive, 10301+index)},
                    'held_cipher': [w for w, covered in zip(held_cipher, mask) if covered],
                    'truth': {'train': words, 'held': [w for w, covered in zip(held, mask) if covered], 'key': key},
                    'key_seed': 10201+index, 'shuffle_seed': 10301+index}
                job['fixture'] = fixture
                if length == 48 and any(f['id'] == fixture['id'] for f in source['fixtures']):
                    old = next(f for f in source['fixtures'] if f['id'] == fixture['id'])
                    assert old == fixture
                    folder = prior.OUT/fixture['id']
                    names = ['prepared.json']+[f'{task}-{suffix}.json' for task in TASKS for suffix in ('result', 'phases')]
                    job['reuse'] = {'folder': str(folder), 'files': {name: digest((folder/name).read_text()) for name in names}}
            jobs.append(job)
    dependencies = [Path(__file__), Path(prior.__file__), Path(prior.baseline.__file__),
                    Path(prior.baseline.engine.__file__), Path(prior.baseline.encoding.__file__)]
    dependencies += list(Path('src/voynich_smt/solver').glob('*.py'))
    dependencies += [Path('src/voynich_smt/language/homophone_patterns.py'), Path('src/voynich_smt/cipher/pattern_shuffle.py')]
    return {'prior_sha256': digest(source), 'source_sha256': digest(raw), 'jobs': jobs,
            'code_sha256': {str(path): digest(path.read_text()) for path in dependencies},
            'scope': 'Seven adaptive matched 48/96-word preceding-context comparisons; original keys, 48-word ciphers and six full holdouts unchanged. Prefix cycle phase aligned per letter. Full broader inventory; default audited. Missing training forms or invalid prefix records gate without replacement. Missing held codes gate individual holdout words only, not fitting. First key only, 30s solver/60s worker per arm; separate observed-key exclusion. Exact old admitted cases reused with file digests. No target dictionary additions. Repeated and overlapping source/holdouts are not independent samples.'}


def prepare():
    p = protocol(); path = OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p, 'Frozen protocol changed'
    else: write_json(path, p)
    return p


def worker(job, task):
    folder = OUT/job
    if task == 'ambiguity': prior.baseline.ambiguity(folder)
    else: prior.baseline.encoding.configure(folder, 'dag'); prior.baseline.engine.fit(task)


def run():
    p = prepare()
    print('Frozen seven matched pairs;', sum(j['admitted'] for j in p['jobs']), 'admitted conditions', flush=True)
    for job in p['jobs']:
        if not job['admitted']: print(job['job'], 'NOT_ADMITTED', flush=True); continue
        fixture = job['fixture']; folder = OUT/job['job']
        write_json(folder/'prepared.json', fixture)
        if job['reuse']:
            source = Path(job['reuse']['folder'])
            for name, sha in job['reuse']['files'].items():
                assert digest((source/name).read_text()) == sha
                if (folder/name).exists(): assert (folder/name).read_bytes() == (source/name).read_bytes()
                else: shutil.copyfile(source/name, folder/name)
            print(job['job'], 'REUSED', flush=True); continue
        for task in TASKS:
            path = folder/f'{task}-result.json'; print(job['job'], task, flush=True)
            if not path.exists():
                start = perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_h2_natural_context', '--worker', job['job'], '--task', task], capture_output=True, text=True, timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter()-start, 'fixture_sha256': digest(fixture)})
            row = json.loads(path.read_text()); print(row['status'], row.get('training_exact'), row.get('held_exact'), flush=True)
    validate()


def validate():
    p = prepare(); rows = []
    for job in p['jobs']:
        row = {k: job[k] for k in ('job', 'pair', 'training_length', 'admitted', 'coverage', 'structural_failures', 'covered_mask')}
        row['reused'] = bool(job['reuse'])
        if not job['admitted']:
            row['status'] = 'NOT_ADMITTED'; rows.append(row); continue
        fixture = job['fixture']; folder = OUT/job['job']
        assert json.loads((folder/'prepared.json').read_text()) == fixture
        a = prior.baseline.compact.load_automaton(fixture['case']['automaton'])
        assert all(a.accepts(w) for w in fixture['truth']['train'])
        assert set(fixture['inventory']) >= {'path', 'sha256'}
        import hashlib
        assert hashlib.sha256(Path(fixture['inventory']['path']).read_bytes()).hexdigest() == fixture['inventory']['sha256']
        results = {}
        for task in TASKS:
            result = json.loads((folder/f'{task}-result.json').read_text()); results[task] = result
            assert result['status'] in ('SAT', 'UNSAT', 'UNKNOWN', 'WALL_TIMEOUT', 'NOT_EVALUATED_NO_SAT')
            if result['status'] in ('SAT', 'UNSAT', 'UNKNOWN'):
                phases = json.loads((folder/f'{task}-phases.json').read_text())
                assert phases['phase'] == 'complete' and phases['timings'] == result['timings']
                assert phases.get('prepared_sha256', phases.get('fixture_sha256')) == digest(fixture)
            if task == 'ambiguity' and 'first_result_sha256' in result:
                assert result['fixture_sha256'] == digest(fixture)
                assert result['first_result_sha256'] == digest(results['positive'])
                if results['positive']['status'] != 'SAT': assert result['status'] == 'NOT_EVALUATED_NO_SAT'
            if result['status'] == 'SAT':
                key = result['alternative_key'] if task == 'ambiguity' else result['recovered_key']
                cipher = fixture['arms']['positive' if task == 'ambiguity' else task]
                assert set(key) == {c for word in cipher for c in word}
                assert max(Counter(key.values()).values()) <= 2
                words = [''.join(key[c] for c in word) for word in cipher]
                assert result['verified'] and words == result['training_words'] and all(a.accepts(w) for w in words)
                if task == 'positive':
                    held = [''.join(key[c] for c in word) for word in fixture['held_cipher']]
                    assert held == result['held_words']
                    assert result['held_exact'] == sum(w == t for w, t in zip(held, fixture['truth']['held']))
                    assert result['training_exact'] == sum(w == t for w, t in zip(words, fixture['truth']['train']))
                if task == 'ambiguity': assert key != results['positive']['recovered_key']
        first = results['positive']; row.update(status=first['status'], training_exact=first.get('training_exact'),
            shuffle_status=results['shuffle']['status'], alternative_status=results['ambiguity']['status'], timings=first.get('timings'))
        if first['status'] == 'SAT':
            scores = evaluate_holdouts(first['recovered_key'], job['full_held_cipher'], job['full_held'])
            assert scores['covered'] == sum(job['covered_mask']) and scores['exact_covered'] == first['held_exact']
            row['holdout_scores'] = scores
            truth = {c: letter for letter, codes in fixture['truth']['key'].items() for c in codes if c in job['observed_codes']}
            row['first_observed_key_exact'] = first['recovered_key'] == truth
            if results['ambiguity']['status'] == 'UNSAT': assert row['first_observed_key_exact']
        else: row['holdout_scores'] = {'status': 'NOT_EVALUATED_NO_SAT', 'covered_before_fit': sum(job['covered_mask'])}
        row['result_sha256'] = {task: digest(result) for task, result in results.items()}
        rows.append(row)
    write_json(OUT/'report.json', {'prepared_sha256': digest(p), 'complete': True, 'conditions': rows})
    write_json(OUT/'validation.json', {'verified': True, 'pairs': 7, 'conditions': 14,
        'admitted': sum(j['admitted'] for j in p['jobs']), 'reused_records': 3*sum(bool(j['reuse']) for j in p['jobs']),
        'new_records': 3*sum(j['admitted'] and not j['reuse'] for j in p['jobs'])})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--worker'); parser.add_argument('--task', choices=TASKS); args = parser.parse_args()
    if args.worker: worker(args.worker, args.task)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
