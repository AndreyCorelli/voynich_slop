"""Matched development searches across training-frequency candidate pool sizes."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
import platform
from pathlib import Path
from statistics import mean
import time

from benchmarks.word_mapping_ablation import load_truth
from benchmarks.word_mapping_recovery import optimize, public_input, resources
from benchmarks.word_mapping_diverse_candidates import diverse_select
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL, file_hashes
from benchmarks.word_mapping_neural_probe import PARENT
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.word_mapping.annealing import Annealer, SearchConfig
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.objective import objective_score

OUT = Path('experiments/results/word-mapping/pool-size-calibration')
SIZES = (512, 2048, None)
BUNDLES = ('bundle-1', 'bundle-2', 'bundle-3')
MODES = ('frequency', 'random', 'lemma-aware')
SEEDS = (101, 202)
METRIC = 'word_normalized_log_sum'


def restrict_catalog(full, morphology, size):
    if size is None:
        return full
    if type(size) is not int or not 1 <= size <= len(full.forms):
        raise ValueError('Invalid candidate pool size')
    # CandidateCatalog only uses counts/analyses, not segment context.
    # Retain original training counts and recompute restricted lemma weights.
    words = tuple(w for w in full.forms[:size] for _ in range(full.form_counts[w]))
    return CandidateCatalog.build([words], morphology, training_sha256=full.training_sha256)


def prepare(parent, model_path, out, *, steps=20000, shortlist=8, resume=False, validate=False):
    if type(steps) is not int or steps < 1 or type(shortlist) is not int or not 6 <= shortlist <= 60:
        raise ValueError('Positive steps and shortlist between 6 and 60 required')
    parent_manifest = json.loads((parent / 'manifest.json').read_text())
    parent_validation = json.loads((parent / 'validation.json').read_text())
    if digest(parent_manifest['protocol']) != parent_manifest['sha256'] or not parent_validation['validated'] or parent_validation['manifest_sha256'] != parent_manifest['sha256']:
        raise ValueError('Validated parent required')
    model, morphology, full = resources(parent / 'bundle-1/foundation')
    if model.identity != parent_manifest['protocol']['model_sha256'] or digest(asdict(full)) != parent_manifest['protocol']['candidate_sha256']:
        raise ValueError('Parent training assets changed')
    catalogs = {size or len(full.forms): restrict_catalog(full, morphology, size) for size in SIZES}
    publics = {}
    for bundle in BUNDLES:
        public = public_input(parent / bundle / 'study/fixtures/one-to-one.json')
        fixture_hash = json.loads((parent / bundle / 'study/manifest.json').read_text())['protocol']['fixture_sha256']['one-to-one']
        if public.identity != fixture_hash:
            raise ValueError('Public fixture changed')
        if len({w for s in public.segments for w in s}) > min(catalogs):
            raise ValueError('Candidate pool too small for injective assignment')
        publics[bundle] = public
    asset = json.loads((model_path / 'manifest.json').read_text())
    if digest(asset['protocol']) != asset['sha256'] or file_hashes(model_path) != asset['protocol']['files_sha256']:
        raise ValueError('Pinned neural model changed')
    paths = [Path(__file__), Path('benchmarks/word_mapping_diverse_candidates.py'),
        Path('benchmarks/word_mapping_recovery.py'), Path('src/voynich_smt/neural_scoring.py'),
        *sorted(Path('src/voynich_smt/word_mapping').glob('*.py'))]
    protocol = {'version': 1, 'parent_sha256': parent_manifest['sha256'],
        'model_sha256': model.identity, 'neural_model_sha256': asset['sha256'],
        'public_sha256': {b: p.identity for b, p in publics.items()},
        'candidate_sha256': {str(n): digest(asdict(c)) for n, c in catalogs.items()},
        'sizes': list(catalogs), 'modes': list(MODES), 'seeds': list(SEEDS),
        'steps': steps, 'archive_size': 10, 'shortlist': shortlist, 'injective': True,
        'metric': METRIC, 'context': 'full-segment', 'threads': 4, 'batch_size': 16,
        'device': 'cpu', 'dtype': 'float32', 'python': platform.python_version(),
        'packages': {n: importlib.metadata.version(n) for n in ('torch', 'transformers', 'tokenizers', 'safetensors')},
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scope': 'three separate development bundles; truth evaluation only; final test unscored'}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    if (out / 'manifest.json').exists():
        if not (resume or validate) or json.loads((out / 'manifest.json').read_text()) != manifest:
            raise ValueError('Output exists or protocol changed')
    elif validate:
        raise ValueError('Missing experiment')
    else:
        write_json(out / 'manifest.json', manifest)
    return model, catalogs, publics, manifest


def config_for(public, mode, seed, steps):
    return SearchConfig(seed=seed, restarts=1, steps_per_restart=steps,
        active_types=len({w for s in public.segments for w in s}),
        initialization=mode, injective=True, archive_size=10)


def searches(model, catalogs, publics, out, manifest, *, validate=False, resume=False):
    hashes = {}
    steps = manifest['protocol']['steps']
    for bundle, public in publics.items():
        for size, catalog in catalogs.items():
            for mode in MODES:
                for seed in SEEDS:
                    label = f'{bundle}/pool-{size}/{mode}-{seed}'
                    directory = out / 'searches' / label
                    config = config_for(public, mode, seed, steps)
                    if validate:
                        search = Annealer(model, catalog, public.segments, config, input_sha256=public.identity).resume(directory / 'checkpoint.json')
                        if not search.complete or search.evaluations != steps:
                            raise ValueError('Search incomplete')
                        archive = json.loads((directory / 'archive.json').read_text())
                        if digest(archive) != digest({'forms': list(catalog.forms), 'rows': search.archive}):
                            raise ValueError('Archive/checkpoint mismatch')
                        for row in archive['rows']:
                            objective = objective_score(model, public.segments, WordMapping(catalog.forms, row['assignments']), injective=True)
                            if not math.isclose(objective, row['score'], abs_tol=1e-8, rel_tol=1e-12):
                                raise ValueError('Archived objective differs')
                    else:
                        optimize(model, catalog, public, config, directory, resume=resume, checkpoint_every=steps)
                        archive = json.loads((directory / 'archive.json').read_text())
                    hashes[label] = digest(archive)
                    print(f"{'Validated' if validate else 'Searched'} {label}", flush=True)
    report = {'manifest_sha256': manifest['sha256'], 'archives': hashes,
        'searches': len(hashes), 'mutations': len(hashes) * steps}
    if validate:
        if json.loads((out / 'search-report.json').read_text()) != report:
            raise ValueError('Search report changed')
    else:
        write_json(out / 'search-report.json', report)
    return report



def selection(catalogs, publics, out, manifest):
    search_report = json.loads((out / 'search-report.json').read_text())
    if search_report['manifest_sha256'] != manifest['sha256']:
        raise ValueError('Search belongs to another protocol')
    jobs = []
    for bundle, public in publics.items():
        for size, catalog in catalogs.items():
            pool = []
            for mode in MODES:
                for seed in SEEDS:
                    label = f'{bundle}/pool-{size}/{mode}-{seed}'
                    archive = json.loads((out / 'searches' / label / 'archive.json').read_text())
                    if digest(archive) != search_report['archives'][label] or archive['forms'] != list(catalog.forms):
                        raise ValueError('Search archive changed')
                    for rank, row in enumerate(archive['rows']):
                        if len(set(row['assignments'].values())) != len(row['assignments']):
                            raise ValueError('Noninjective dictionary')
                        pool.append({**row, 'origin': f'{mode}-{seed}', 'origin_rank': rank})
            selected = diverse_select(pool, manifest['protocol']['shortlist'])
            candidates = []
            for rank, row in enumerate(selected):
                segments = WordMapping(catalog.forms, row['assignments']).render(public.segments)
                if any(w is None for s in segments for w in s):
                    raise ValueError('Incomplete dictionary')
                candidates.append({'rank': rank, **row, 'segments': segments})
            jobs.append({'id': f'{bundle}-pool-{size}', 'bundle': bundle, 'size': size,
                'pool': pool, 'candidates': candidates})
    return json.loads(json.dumps(jobs))


def summaries(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['size']].append(row)
    return [{'size': size, 'cases': len(group),
        'mean_candidate_token_coverage': mean(r['candidate_token_coverage'] for r in group),
        'mean_ngram_accuracy': mean(r['ngram']['exact_token_accuracy'] for r in group),
        'mean_neural_accuracy': mean(r['neural']['exact_token_accuracy'] for r in group),
        'mean_shortlist_oracle_accuracy': mean(r['shortlist_oracle_accuracy'] for r in group),
        'mean_pool_oracle_accuracy': mean(r['pool_oracle_accuracy'] for r in group),
        'improved': sum(r['neural']['exact_token_accuracy'] > r['ngram']['exact_token_accuracy'] for r in group),
        'worsened': sum(r['neural']['exact_token_accuracy'] < r['ngram']['exact_token_accuracy'] for r in group)} for size, group in sorted(groups.items())]


def rerank(catalogs, publics, parent, model_path, out, manifest, *, validate=False, resume=False):
    jobs = selection(catalogs, publics, out, manifest)
    if (out / 'selection.json').exists():
        if json.loads((out / 'selection.json').read_text()) != jobs:
            raise ValueError('Frozen shortlist changed')
    elif validate:
        raise ValueError('Missing selection')
    else:
        write_json(out / 'selection.json', jobs)
    scorer = WholeWordScorer.load(model_path / 'inference', batch_size=16, threads=4)
    rows = []
    for job in jobs:
        scored = []
        for candidate in job['candidates']:
            path = out / 'scores' / f"{job['id']}-{candidate['rank']}.json"
            saved = json.loads(path.read_text()) if path.exists() else None
            if saved and digest(saved['row']) != saved['sha256']:
                raise ValueError('Neural row checksum differs')
            if saved and resume and not validate:
                row = saved['row']
            else:
                start = time.perf_counter()
                before = scorer.inference_rows
                score = scorer.score(candidate['segments'])
                row = {'candidate_sha256': digest(candidate), 'score': score,
                    'seconds': time.perf_counter() - start, 'masked_words': scorer.inference_rows - before}
                if validate:
                    if not saved or row['candidate_sha256'] != saved['row']['candidate_sha256']:
                        raise ValueError('Missing or changed scored candidate')
                    if any(not math.isclose(v, saved['row']['score'][k], abs_tol=1e-4, rel_tol=1e-6) for k, v in score.items()):
                        raise ValueError('Neural score differs from recomputation')
                    row = saved['row']
                else:
                    write_json(path, {'row': row, 'sha256': digest(row)})
            if row['candidate_sha256'] != digest(candidate):
                raise ValueError('Neural row identity changed')
            scored.append(row)
            print(f"{'Validated' if validate else 'Scored'} {job['id']} rank {candidate['rank']}", flush=True)
        selected = max(range(len(scored)), key=lambda i: (scored[i]['score'][METRIC], -i))
        # Truth enters only after all search, shortlist selection and neural ranking.
        public = publics[job['bundle']]
        catalog = catalogs[job['size']]
        truth = load_truth(parent / job['bundle'] / 'study', 'one-to-one')
        pool_recovery = [recovery(public, truth, WordMapping(catalog.forms, r['assignments'])) for r in job['pool']]
        candidate_recovery = [recovery(public, truth, WordMapping(catalog.forms, r['assignments'])) for r in job['candidates']]
        tokens = [w for s in truth.plaintext for w in s]
        supported = set(catalog.forms)
        coverage = sum(w in supported for w in tokens) / len(tokens)
        ngram, neural = candidate_recovery[0], candidate_recovery[selected]
        rows.append({'id': job['id'], 'bundle': job['bundle'], 'size': job['size'],
            'truth_sha256': digest(asdict(truth)), 'candidate_token_coverage': coverage,
            'candidate_type_coverage': len(set(tokens) & supported) / len(set(tokens)),
            'selected_rank': selected, 'selected_origin': job['candidates'][selected]['origin'],
            'ngram': ngram, 'neural': neural,
            'ngram_accuracy_on_supported_tokens': ngram['exact_token_accuracy'] / coverage if coverage else None,
            'neural_accuracy_on_supported_tokens': neural['exact_token_accuracy'] / coverage if coverage else None,
            'shortlist_oracle_accuracy': max(r['exact_token_accuracy'] for r in candidate_recovery),
            'pool_oracle_accuracy': max(r['exact_token_accuracy'] for r in pool_recovery),
            'distinct_pool_dictionaries': len({digest(r['assignments']) for r in job['pool']}),
            'scoring_seconds': sum(r['seconds'] for r in scored),
            'masked_words': sum(r['masked_words'] for r in scored)})
        scorer.cache.clear()
    report = {'manifest_sha256': manifest['sha256'], 'selection_sha256': digest(jobs),
        'rows': rows, 'summary': summaries(rows),
        'scope': manifest['protocol']['scope'], 'dictionaries': sum(len(j['candidates']) for j in jobs)}
    if validate:
        if json.loads((out / 'report.json').read_text()) != report:
            raise ValueError('Recovery report differs')
        write_json(out / 'validation.json', {'validated': True, 'manifest_sha256': manifest['sha256'],
            'dictionaries': report['dictionaries'], 'recomputed_masked_words': scorer.inference_rows})
    else:
        write_json(out / 'report.json', report)
    print(json.dumps(report['summary'], indent=2), flush=True)
    return report


def run(parent=PARENT, model_path=DEFAULT_MODEL, out=OUT, *, phase='all', steps=20000,
        shortlist=8, resume=False, validate=False):
    parent, model_path, out = map(Path, (parent, model_path, out))
    if phase not in ('all', 'search', 'rerank') or (validate and phase != 'all'):
        raise ValueError('Validation must include all phases')
    model, catalogs, publics, manifest = prepare(parent, model_path, out, steps=steps,
        shortlist=shortlist, resume=resume, validate=validate)
    if phase in ('all', 'search'):
        searches(model, catalogs, publics, out, manifest, validate=validate, resume=resume)
    if phase in ('all', 'rerank'):
        return rerank(catalogs, publics, parent, model_path, out, manifest, validate=validate, resume=resume)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--model', type=Path, default=DEFAULT_MODEL)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--steps', type=int, default=20000)
    parser.add_argument('--shortlist', type=int, default=8)
    parser.add_argument('--phase', choices=('all', 'search', 'rerank'), default='all')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    run(args.parent, args.model, args.out, phase=args.phase, steps=args.steps,
        shortlist=args.shortlist, resume=args.resume, validate=args.validate)
