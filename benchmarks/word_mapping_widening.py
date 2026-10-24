"""Nested natural-text widening with fixed scoring and frozen-occurrence holdout."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import random
from statistics import mean
import time

from benchmarks.word_mapping_long_context import PARENT as ORIGINAL
from benchmarks.word_mapping_recovery import public_input
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.widening_mapping import WideningSearch, expanded_model, nested_prefixes, repetition_statistics
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.corpora import WordStream, validate_splits
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.fixtures import CipherInput, CipherTruth, generate
from voynich_smt.word_mapping.incremental import IncrementalScorer
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.ngram import BOS, EOS, NgramModel
from voynich_smt.word_mapping.objective import objective_score

PARENT = Path('experiments/results/word-mapping/long-context-calibration')
OUT = Path('experiments/results/word-mapping/widening-calibration')
TARGETS = (500, 2000, 8000, 16000, 32000)
SEEDS = (101, 202)
_WORKER = None


def source_streams(parent):
    """Reassign entire books before training; never use old trained counts."""
    parent = Path(parent)
    saved = json.loads((parent / 'manifest.json').read_text())
    validated = json.loads((parent / 'validation.json').read_text())
    if digest(saved['protocol']) != saved['sha256'] or not validated['validated'] or validated['manifest_sha256'] != saved['sha256']:
        raise ValueError('Validated source parent required')
    foundation = parent / 'bundle-1/foundation'
    original_train = WordStream.load(foundation / 'splits/train.json')
    original_morphology = MorphologyCatalog.load(foundation / 'morphology-training.json')
    if original_train.identity != saved['protocol']['training_sha256'] or original_morphology.identity != saved['protocol']['morphology_sha256']:
        raise ValueError('Changed source training resources')
    full = WordStream.load(ORIGINAL / 'corpora/caesar-full.json')
    test = WordStream.load(ORIGINAL / 'splits/test.json')
    if test.identity != saved['protocol']['test_sha256']:
        raise ValueError('Changed original final test')
    blocked = {(r.source_id, r.record_index) for r in test.records if r.surface is not None}
    gallic = full.select(lambda r: (r.source_id, r.record_index) not in blocked,
        description={'policy': 'Gallic I-IV except original final test positions; no coverage screening'})
    reserved = {'caesar-extension-bc1', 'caesar-extension-bc2'}
    train = WordStream(tuple(r for r in original_train.records if r.source_id not in reserved),
        {'original_train_sha256': original_train.identity,
         'policy': 'Gallic V-VII and Civil III only; Civil I-II reassigned to development'})
    development = WordStream(gallic.records + tuple(r for r in original_train.records if r.source_id in reserved),
        {'gallic_sha256': gallic.identity, 'original_train_sha256': original_train.identity,
         'policy': 'Gallic I-IV then Civil I-II; original test excluded; no screening'})
    return train, development, test, original_morphology, saved['sha256']


def jobs_for(publics, steps, seeds, restarts):
    if type(steps) is not int or steps < 1 or type(restarts) is not int or restarts < 1:
        raise ValueError('Positive steps and restarts required')
    smallest = len({w for s in publics[min(publics)].segments for w in s})
    jobs = []
    for target, public in publics.items():
        types = len({w for s in public.segments for w in s})
        scaled = math.ceil(steps * types / smallest)
        by_steps = defaultdict(list)
        by_steps[steps].append('equal')
        by_steps[scaled].append('scaled')
        for coverage in ('training', 'oracle'):
            for seed in seeds:
                for budget, modes in by_steps.items():
                    config = SearchConfig(seed=seed, restarts=restarts, steps_per_restart=budget,
                        active_types=types, initialization='mixed', injective=True, archive_size=1)
                    jobs.append({'target': target, 'coverage': coverage, 'seed': seed,
                        'budget_modes': modes, 'config': asdict(config),
                        'label': f'{target}/{coverage}/seed-{seed}/steps-{budget}'})
    return jobs


def prepare(parent, out, *, targets=TARGETS, holdout_tokens=2048, steps=20000, seeds=SEEDS,
            restarts=3, resume=False, validate=False):
    out = Path(out)
    train, development, test, old_morphology, parent_sha = source_streams(parent)
    split_hashes = validate_splits({'train': train, 'development': development, 'test': test})
    prefixes, holdout = nested_prefixes(development.segments(), targets, holdout_tokens=holdout_tokens)
    base_model = NgramModel.train(train.segments(), training_sha256=train.identity)
    all_forms = {w for s in development.segments() for w in s}
    model = expanded_model(base_model, all_forms)
    # Timeless dictionary analyses may be reused; no old corpus counts survive.
    entries = {w: old_morphology.entries.get(w, []) for w in base_model.vocabulary}
    entries.update({w: [] for w in all_forms if w not in entries})
    morphology = MorphologyCatalog(entries,
        {**old_morphology.resource, 'cache_source_sha256': old_morphology.identity,
         'extra_form_policy': 'oracle unseen surfaces have no analyses'}, train.identity,
        annotation_failures={w: reason for w, reason in old_morphology.annotation_failures.items() if w in base_model.vocabulary})
    training = CandidateCatalog.build(train.segments(), morphology, training_sha256=train.identity)
    extra = sorted(all_forms - set(training.forms))
    oracle = replace(training, forms=training.forms + tuple(extra),
                     form_counts={**training.form_counts, **{w: 0 for w in extra}})
    candidates = {'training': training, 'oracle': oracle}
    largest = prefixes[max(prefixes)]
    combined_public, combined_truth = generate(largest + holdout,
        source={'development_sha256': development.identity, 'policy': 'shared codebook across nested fits and holdout'}, seed=7331)
    def fixture(plain, cipher, label):
        public = CipherInput(tuple(cipher), {'development_sha256': development.identity, 'part': label}, combined_public.encoder)
        truth = CipherTruth(public.identity, tuple(plain),
            {w: combined_truth.decoding[w] for s in cipher for w in s}, 1.0)
        return public, truth
    publics, truths = {}, {}
    for target, plain in prefixes.items():
        publics[target], truths[target] = fixture(plain, combined_public.segments[:len(plain)], f'fit-{target}')
    held_public, held_truth = fixture(holdout, combined_public.segments[len(largest):], 'holdout')
    jobs = jobs_for(publics, steps, seeds, restarts)
    paths = [Path(__file__), Path('src/voynich_smt/widening_mapping.py'),
             Path('src/voynich_smt/bootstrap_mapping.py'), Path('benchmarks/word_mapping_recovery.py'),
             *sorted(Path('src/voynich_smt/word_mapping').glob('*.py'))]
    protocol = {'version': 1, 'parent_sha256': parent_sha, 'splits': split_hashes,
        'targets': list(targets), 'holdout_tokens_requested': holdout_tokens,
        'base_steps': steps, 'seeds': list(seeds), 'restarts': restarts,
        'model_sha256': model.identity, 'morphology_sha256': morphology.identity,
        'candidates_sha256': {k: digest(asdict(c)) for k, c in candidates.items()},
        'public_sha256': {str(k): p.identity for k, p in publics.items()},
        'holdout_sha256': held_public.identity, 'jobs': jobs,
        'oracle_policy': 'fixed pool contains all development forms including holdout; no counts or decoding key provided',
        'objective_policy': 'one fixed smoothed n-gram model; extras have distinct zero-count IDs; no morphology score',
        'scope': 'same-author disjoint books; nested whole scored segments; original final test unscored',
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    protocol = json.loads(json.dumps(protocol))
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    path = out / 'manifest.json'
    if path.exists():
        if not (resume or validate) or json.loads(path.read_text()) != manifest:
            raise ValueError('Output exists or protocol changed')
    elif validate:
        raise ValueError('Missing widening experiment')
    exported = {'manifest.json': manifest, 'morphology.json': {**morphology.artifact(), 'sha256': morphology.identity},
        'model.json': {**model.artifact(), 'sha256': model.identity},
        'public/holdout.json': asdict(held_public), 'truth/holdout.json': asdict(held_truth)}
    for name, candidate in candidates.items():
        exported[f'candidates-{name}.json'] = asdict(candidate)
    for target, public in publics.items():
        exported[f'public/fit-{target}.json'] = asdict(public)
        exported[f'truth/fit-{target}.json'] = asdict(truths[target])
    for name, value in exported.items():
        if validate:
            if digest(json.loads((out / name).read_text())) != digest(value):
                raise ValueError(f'Foundation export differs: {name}')
        else:
            write_json(out / name, value)
    for name, stream in (('train', train), ('development', development), ('test', test)):
        path = out / f'splits/{name}.json'
        if validate:
            if WordStream.load(path).identity != stream.identity:
                raise ValueError('Saved split differs')
        else:
            stream.save(path)
    foundation = {'manifest_sha256': manifest['sha256'], 'training_tokens': sum(map(len, train.segments())),
        'development_tokens': sum(map(len, development.segments())), 'holdout_tokens': sum(map(len, holdout)),
        'candidate_forms': {name: len(c.forms) for name, c in candidates.items()},
        'zero_count_forms': len(extra), 'cases': {str(k): repetition_statistics(p.segments, held_public.segments) for k, p in publics.items()},
        'unique_searches': len(jobs), 'evaluations': sum(j['config']['restarts']*j['config']['steps_per_restart'] for j in jobs)}
    if validate:
        if json.loads((out / 'foundation-report.json').read_text()) != foundation:
            raise ValueError('Foundation report differs')
    else:
        write_json(out / 'foundation-report.json', foundation)
    return model, morphology, candidates, publics, held_public, manifest, foundation


def load_candidates(path):
    value = json.loads(Path(path).read_text())
    value['forms'] = tuple(value['forms'])
    value['lemma_forms'] = {k: tuple(v) for k, v in value['lemma_forms'].items()}
    return CandidateCatalog(**value)


def initialize_worker(out):
    global _WORKER
    out = Path(out)
    _WORKER = (NgramModel.load(out / 'model.json'), MorphologyCatalog.load(out / 'morphology.json'),
        {name: load_candidates(out / f'candidates-{name}.json') for name in ('training', 'oracle')})


def search_worker(out, job, resume):
    model, morphology, catalogs = _WORKER
    out = Path(out)
    candidate = catalogs[job['coverage']]
    public = public_input(out / f'public/fit-{job["target"]}.json')
    config = SearchConfig(**job['config'])
    search = WideningSearch(model, candidate, morphology, public.segments, config, input_sha256=public.identity)
    directory = out / 'runs' / job['label']
    trace = []
    seconds = 0.0
    if (directory / 'checkpoint.json').exists():
        if not resume:
            raise ValueError('Run already exists')
        search.resume(directory / 'checkpoint.json')
        if (directory / 'trace.json').exists():
            saved = json.loads((directory / 'trace.json').read_text())
            if digest(saved['rows']) != saved['sha256']:
                raise ValueError('Trace checksum differs')
            trace = [r for r in saved['rows'] if r['evaluations'] <= search.evaluations]
            seconds = trace[-1]['seconds'] if trace else 0.0
    def record():
        nonlocal trace
        row = {'evaluations': search.evaluations, 'best_score': search.archive[0]['score'],
               'current_score': search.scorer.objective, 'seconds': seconds}
        if trace and trace[-1]['evaluations'] == search.evaluations:
            trace[-1] = row
        else:
            trace.append(row)
        search.checkpoint(directory / 'checkpoint.json')
        write_json(directory / 'trace.json', {'rows': trace, 'sha256': digest(trace)})
    if not trace:
        record()
    chunk = max(1, config.steps_per_restart // 4)
    while not search.complete:
        started = time.perf_counter()
        search.advance(chunk)
        seconds += time.perf_counter() - started
        record()
    archive = {'forms': list(candidate.forms), 'rows': search.archive}
    report = {'job': job, 'search_sha256': search.identity, 'evaluations': search.evaluations,
              'archive_sha256': digest(archive), 'statistics': search.statistics,
              'seconds': seconds, 'trace_sha256': digest(trace)}
    write_json(directory / 'archive.json', archive)
    write_json(directory / 'search-report.json', report)
    return report


def validate_search(out, job, model, morphology, catalogs, publics):
    directory = Path(out) / 'runs' / job['label']
    public, candidate = publics[job['target']], catalogs[job['coverage']]
    config = SearchConfig(**job['config'])
    search = WideningSearch(model, candidate, morphology, public.segments, config, input_sha256=public.identity).resume(directory / 'checkpoint.json')
    if not search.complete or search.evaluations != config.restarts*config.steps_per_restart:
        raise ValueError('Incomplete widening checkpoint')
    saved = json.loads((directory / 'search-report.json').read_text())
    archive = json.loads((directory / 'archive.json').read_text())
    if archive != {'forms': list(candidate.forms), 'rows': search.archive} or saved['archive_sha256'] != digest(archive):
        raise ValueError('Archive/checkpoint differs')
    if saved['job'] != job or saved['search_sha256'] != search.identity or saved['evaluations'] != search.evaluations or saved['statistics'] != search.statistics:
        raise ValueError('Search report differs')
    for row in archive['rows']:
        full = objective_score(model, public.segments, WordMapping(candidate.forms, row['assignments']), injective=True)
        if not math.isclose(full, row['score'], abs_tol=1e-7, rel_tol=1e-12):
            raise ValueError('Independent archive objective differs')
    trace = json.loads((directory / 'trace.json').read_text())
    rows = trace['rows']
    if not rows or digest(rows) != trace['sha256'] or trace['sha256'] != saved['trace_sha256']:
        raise ValueError('Saved trace differs')
    if rows[-1]['evaluations'] != search.evaluations or rows[-1]['seconds'] != saved['seconds'] or not math.isclose(rows[-1]['best_score'], search.archive[0]['score'], abs_tol=1e-8):
        raise ValueError('Trace endpoint differs')
    if any(b['evaluations'] <= a['evaluations'] or b['best_score'] < a['best_score']-1e-8 or b['seconds'] < a['seconds'] for a, b in zip(rows, rows[1:])):
        raise ValueError('Nonmonotonic trace')
    return saved


def search_phase(out, manifest, model, morphology, candidates, publics, *, workers=4, resume=False, validate=False):
    if type(workers) is not int or workers < 1:
        raise ValueError('Positive worker count required')
    jobs = manifest['protocol']['jobs']
    reports = {}
    if validate:
        for job in jobs:
            reports[job['label']] = validate_search(out, job, model, morphology, candidates, publics)
    elif workers == 1:
        initialize_worker(out)
        for job in jobs:
            reports[job['label']] = search_worker(out, job, resume)
            print(f'Searched {len(reports)}/{len(jobs)} {job["label"]}', flush=True)
    else:
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context('spawn'), initializer=initialize_worker, initargs=(out,)) as pool:
            futures = {pool.submit(search_worker, out, job, resume): job for job in jobs}
            for future in as_completed(futures):
                job = futures[future]
                reports[job['label']] = future.result()
                write_json(Path(out) / 'progress.json', {'completed': len(reports), 'planned': len(jobs), 'evaluations': sum(r['evaluations'] for r in reports.values())})
                print(f'Searched {len(reports)}/{len(jobs)} {job["label"]}', flush=True)
    report = {'manifest_sha256': manifest['sha256'], 'runs': {k: digest(v) for k, v in sorted(reports.items())},
              'searches': len(reports), 'evaluations': sum(r['evaluations'] for r in reports.values())}
    path = Path(out) / 'search-report.json'
    if validate:
        if json.loads(path.read_text()) != report:
            raise ValueError('Search phase report differs')
    else:
        write_json(path, report)
    return reports


def load_truth(path):
    value = json.loads(Path(path).read_text())
    value['plaintext'] = tuple(tuple(s) for s in value['plaintext'])
    return CipherTruth(**value)


def accuracy_subset(public, truth, mapping, eligible):
    guesses = mapping.render(public.segments)
    hits = total = 0
    for cipher, predicted, gold in zip(public.segments, guesses, truth.plaintext):
        for word, guess, actual in zip(cipher, predicted, gold):
            if eligible(word, actual):
                total += 1
                hits += guess == actual
    return {'tokens': total, 'correct': hits, 'accuracy': hits / total if total else None}


def held_event_comparison(model, public, truth, mapping):
    """Compare the same real prediction events; unknown context causes exclusion.

    Never introduce synthetic EOS/BOS around unmapped holdout words.
    """
    predicted = actual = 0.0
    events = 0
    for segment in public.segments:
        a = b = BOS
        for c in (*segment, EOS):
            terms = (a, b, c)
            if all(not isinstance(w, str) or mapping.assignments.get(w) is not None for w in terms):
                ids = [w if isinstance(w, int) else model.form_ids[mapping.forms[mapping.assignments[w]]] for w in terms]
                gold = [w if isinstance(w, int) else model.form_ids[truth.decoding[w]] for w in terms]
                predicted += math.log(model.probability(*ids))
                actual += math.log(model.probability(*gold))
                events += 1
            a, b = b, c
    return {'events': events, 'prediction_log_score': predicted, 'truth_log_score': actual,
            'score_gap_per_event': (predicted-actual)/events if events else None}


def local_truth_audit(model, public, truth, forms):
    """Sample one-change/swap neighbors after main search, explicitly using truth."""
    ids = {w: i for i, w in enumerate(forms)}
    gold = WordMapping(forms, {w: ids[f] for w, f in truth.decoding.items()})
    scorer = IncrementalScorer(model, public.segments, gold, injective=True)
    owners = {f: w for w, f in gold.assignments.items()}
    counts = Counter(w for s in public.segments for w in s)
    frequent = sorted(counts, key=lambda w: (-counts[w], w))[:128]
    remaining = sorted(counts.keys()-set(frequent))
    rng = random.Random(9441)
    words = frequent + rng.sample(remaining, min(128, len(remaining)))
    tested = improving = ties = 0
    best_delta = 0.0
    best_changes = {}
    for word in words:
        alternatives = set(range(min(16, len(forms)))) | set(rng.sample(range(len(forms)), min(16, len(forms))))
        alternatives.discard(gold.assignments[word])
        for form in sorted(alternatives):
            changes = {word: form}
            owner = owners.get(form)
            if owner is not None:
                changes[owner] = gold.assignments[word]
            proposal = scorer.propose(changes)
            delta = scorer.delta(proposal)
            tested += 1
            improving += delta > 1e-9
            ties += abs(delta) <= 1e-9
            if delta > best_delta:
                best_delta, best_changes = delta, changes
    full = objective_score(model, public.segments, WordMapping(forms, {**gold.assignments, **best_changes}), injective=True)
    if not math.isclose(full-scorer.objective, best_delta, abs_tol=1e-7, rel_tol=1e-10):
        raise ValueError('Truth diagnostic full-score mismatch')
    return {'types_examined': len(words), 'proposals': tested, 'improving_neighbors': improving,
        'tied_neighbors': ties, 'largest_improvement': best_delta, 'best_changes': best_changes,
        'scope': 'sampled local oracle diagnostic; not an exhaustive or realistic search'}


def evaluate(out, manifest, model, candidates, publics, held_public, reports):
    out = Path(out)
    phase = json.loads((out / 'search-report.json').read_text())
    if phase['manifest_sha256'] != manifest['sha256'] or phase['searches'] != len(manifest['protocol']['jobs']):
        raise ValueError('Complete matched searches required before truth evaluation')
    held_truth = load_truth(out / 'truth/holdout.json')
    training_forms = set(candidates['training'].forms)
    rows, diagnostics = [], {}
    for target, public in publics.items():
        truth = load_truth(out / f'truth/fit-{target}.json')
        full_catalog = candidates['oracle']
        ids = {f: i for i, f in enumerate(full_catalog.forms)}
        gold = WordMapping(full_catalog.forms, {w: ids[f] for w, f in truth.decoding.items()})
        gold_score = objective_score(model, public.segments, gold, injective=True)
        events = sum(map(len, public.segments)) + len(public.segments)
        counts = Counter(w for s in public.segments for w in s)
        diagnostics[str(target)] = local_truth_audit(model, public, truth, full_catalog.forms)
        for job in manifest['protocol']['jobs']:
            if job['target'] != target:
                continue
            saved = reports[job['label']]
            if phase['runs'][job['label']] != digest(saved):
                raise ValueError('Run changed before evaluation')
            archive = json.loads((out / 'runs' / job['label'] / 'archive.json').read_text())
            if digest(archive) != saved['archive_sha256']:
                raise ValueError('Archive changed before evaluation')
            candidate = candidates[job['coverage']]
            mapping = WordMapping(candidate.forms, archive['rows'][0]['assignments'])
            metrics = recovery(public, truth, mapping)
            repeated = accuracy_subset(public, truth, mapping, lambda w, f: counts[w] >= 2)
            common = accuracy_subset(public, truth, mapping, lambda w, f: counts[w] >= 5)
            known = accuracy_subset(public, truth, mapping, lambda w, f: f in training_forms)
            held = accuracy_subset(held_public, held_truth, mapping, lambda w, f: w in counts)
            held_known = accuracy_subset(held_public, held_truth, mapping, lambda w, f: w in counts and f in training_forms)
            candidate_forms = set(candidate.forms)
            supported = sum(n for w, n in counts.items() if truth.decoding[w] in candidate_forms)
            rows.append({'job': job, 'recovery': metrics, 'fit_repeated': repeated, 'fit_common': common,
                'fit_training_attested': known, 'holdout_recurring': held, 'holdout_recurring_training_attested': held_known,
                'holdout_unseen_tokens': sum(map(len, held_public.segments))-held['tokens'],
                'candidate_token_coverage': supported / metrics['tokens'],
                'best_score': archive['rows'][0]['score'], 'truth_score': gold_score,
                'fit_score_gap_per_event': (archive['rows'][0]['score']-gold_score)/events,
                'holdout_events': held_event_comparison(model, held_public, held_truth, mapping),
                'seconds': saved['seconds'], 'evaluations': saved['evaluations'],
                'archive_sha256': saved['archive_sha256']})
    summary = []
    for target in publics:
        for coverage in candidates:
            for mode in ('equal', 'scaled'):
                values = [r for r in rows if r['job']['target'] == target and r['job']['coverage'] == coverage and mode in r['job']['budget_modes']]
                summary.append({'target': target, 'coverage': coverage, 'budget_mode': mode, 'runs': len(values),
                    'steps_per_restart': values[0]['job']['config']['steps_per_restart'],
                    'mean_token_accuracy': mean(r['recovery']['exact_token_accuracy'] for r in values),
                    'mean_type_accuracy': mean(r['recovery']['exact_type_accuracy'] for r in values),
                    'mean_training_attested_accuracy': mean(r['fit_training_attested']['accuracy'] for r in values),
                    'mean_common_accuracy': mean(r['fit_common']['accuracy'] for r in values if r['fit_common']['accuracy'] is not None) if any(r['fit_common']['accuracy'] is not None for r in values) else None,
                    'mean_holdout_recurring_accuracy': mean(r['holdout_recurring']['accuracy'] for r in values if r['holdout_recurring']['accuracy'] is not None) if any(r['holdout_recurring']['accuracy'] is not None for r in values) else None,
                    'candidate_token_coverage': values[0]['candidate_token_coverage'],
                    'wrong_mapping_outscores_truth_runs': sum(r['fit_score_gap_per_event'] > 1e-9 for r in values),
                    'mean_score_gap_per_event': mean(r['fit_score_gap_per_event'] for r in values)})
    return {'manifest_sha256': manifest['sha256'], 'rows': rows, 'summary': summary,
        'truth_neighborhood_diagnostics': diagnostics, 'unique_searches': phase['searches'],
        'evaluations': phase['evaluations'], 'scope': manifest['protocol']['scope']}


def run(parent=PARENT, out=OUT, *, targets=TARGETS, holdout_tokens=2048, steps=20000,
        seeds=SEEDS, restarts=3, workers=4, resume=False, validate=False, prepare_only=False):
    model, morphology, candidates, publics, held, manifest, foundation = prepare(parent, out,
        targets=targets, holdout_tokens=holdout_tokens, steps=steps, seeds=seeds, restarts=restarts, resume=resume, validate=validate)
    print(json.dumps(foundation, indent=2), flush=True)
    if prepare_only:
        return foundation
    reports = search_phase(out, manifest, model, morphology, candidates, publics, workers=workers, resume=resume, validate=validate)
    report = evaluate(out, manifest, model, candidates, publics, held, reports)
    path = Path(out) / 'report.json'
    if validate:
        if json.loads(path.read_text()) != report:
            raise ValueError('Recomputed widening evaluation differs')
        write_json(Path(out) / 'validation.json', {'validated': True, 'manifest_sha256': manifest['sha256'],
            'searches': report['unique_searches'], 'evaluations': report['evaluations'], 'report_sha256': digest(report)})
    else:
        write_json(path, report)
    print(json.dumps(report['summary'], indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--steps', type=int, default=20000)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    run(args.parent, args.out, steps=args.steps, workers=args.workers,
        resume=args.resume, validate=args.validate, prepare_only=args.prepare_only)
