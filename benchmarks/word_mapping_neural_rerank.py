"""Bounded, offline neural reranking of frozen development archives."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import time
from pathlib import Path
from statistics import mean

from benchmarks.word_mapping_ablation import load_truth
from benchmarks.word_mapping_recovery import public_input
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL, file_hashes
from benchmarks.word_mapping_neural_probe import PARENT
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.evaluation import recovery

METRIC = 'word_normalized_log_sum'


def freeze(parent, top):
    if type(top) is not int or not 1 <= top <= 30:
        raise ValueError('top must be between 1 and 30')
    manifest = json.loads((parent / 'manifest.json').read_text())
    validation = json.loads((parent / 'validation.json').read_text())
    if digest(manifest['protocol']) != manifest['sha256'] or not validation['validated'] or validation['manifest_sha256'] != manifest['sha256']:
        raise ValueError('Validated parent required')
    jobs = []
    for bundle in ('bundle-1', 'bundle-2', 'bundle-3', 'pooled'):
        study = parent / bundle / 'study'
        public = public_input(study / 'fixtures/one-to-one.json')
        for profile in ('injective', 'trigram'):
            for seed in (11, 22):
                path = study / f'runs/one-to-one/{profile}/seed-{seed}/budget-50000/original/archive.json'
                archive = json.loads(path.read_text())
                rows = archive['rows'][:top]
                if not rows or any(a['score'] < b['score'] for a, b in zip(rows, rows[1:])):
                    raise ValueError('Archive is empty or unsorted')
                candidates = []
                for rank, row in enumerate(rows):
                    mapping = WordMapping(archive['forms'], row['assignments'])
                    segments = mapping.render(public.segments)
                    if any(w is None for s in segments for w in s):
                        raise ValueError('Incomplete dictionary')
                    candidates.append({'rank': rank, 'assignments': row['assignments'], 'segments': segments, 'ngram_score': row['score']})
                jobs.append({'id': f'{bundle}-{profile}-{seed}', 'bundle': bundle, 'profile': profile,
                    'seed': seed, 'public_sha256': public.identity, 'archive_sha256': digest(archive),
                    'forms': archive['forms'], 'candidates': candidates})
    return json.loads(json.dumps(jobs)), manifest['sha256']


def choose(scores):
    # Stable archive rank breaks exact ties. Truth never enters this function.
    return max(range(len(scores)), key=lambda i: (scores[i][METRIC], -i))


def run(parent, model, out, *, top=5, validate=False, resume=False):
    parent, model, out = map(Path, (parent, model, out))
    jobs, parent_hash = freeze(parent, top)
    asset = json.loads((model / 'manifest.json').read_text())
    if digest(asset['protocol']) != asset['sha256'] or file_hashes(model) != asset['protocol']['files_sha256']:
        raise ValueError('Model assets changed')
    protocol = {'version': 1, 'parent_sha256': parent_hash, 'selection_sha256': digest(jobs),
        'model_sha256': asset['sha256'], 'top': top, 'metric': METRIC, 'context': 'full-segment',
        'batch_size': 16, 'threads': 4, 'device': 'cpu', 'dtype': 'float32',
        'python': platform.python_version(),
        'packages': {n: importlib.metadata.version(n) for n in ('torch', 'transformers', 'tokenizers', 'safetensors')},
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (Path(__file__), Path('src/voynich_smt/neural_scoring.py'), Path('src/voynich_smt/word_mapping/evaluation.py'), Path('src/voynich_smt/word_mapping/mapping.py'))}}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    if (out / 'manifest.json').exists():
        if not (validate or resume) or json.loads((out / 'manifest.json').read_text()) != manifest:
            raise ValueError('Output exists or protocol changed')
    elif validate:
        raise ValueError('Missing experiment')
    else:
        write_json(out / 'manifest.json', manifest)
        write_json(out / 'selection.json', jobs)
    if json.loads((out / 'selection.json').read_text()) != jobs:
        raise ValueError('Frozen selection changed')
    scorer = WholeWordScorer.load(model / 'inference', batch_size=16, threads=4)
    reports = []
    for job in jobs:
        scores = []
        for candidate in job['candidates']:
            path = out / 'scores' / f"{job['id']}-{candidate['rank']}.json"
            saved = json.loads(path.read_text()) if path.exists() else None
            if saved and digest(saved['row']) != saved['sha256']:
                raise ValueError('Score checksum changed')
            if saved and resume and not validate:
                row = saved['row']
            else:
                start = time.perf_counter()
                before = scorer.inference_rows
                score = scorer.score(candidate['segments'])
                row = {'candidate_sha256': digest(candidate), 'score': score,
                    'seconds': time.perf_counter() - start, 'masked_words': scorer.inference_rows - before}
                if validate:
                    if saved is None or saved['row']['candidate_sha256'] != row['candidate_sha256']:
                        raise ValueError('Missing or changed candidate')
                    if any(not math.isclose(v, saved['row']['score'][k], abs_tol=1e-4, rel_tol=1e-6) for k, v in score.items()):
                        raise ValueError('Offline recomputation differs')
                    row = saved['row']
                else:
                    write_json(path, {'row': row, 'sha256': digest(row)})
            if row['candidate_sha256'] != digest(candidate):
                raise ValueError('Score belongs to another candidate')
            scores.append(row['score'])
            print(f"{'Validated' if validate else 'Scored'} {job['id']} rank {candidate['rank']}", flush=True)
        selected = choose(scores)
        # Evaluation only after the scorer has selected its winner.
        study = parent / job['bundle'] / 'study'
        public = public_input(study / 'fixtures/one-to-one.json')
        truth = load_truth(study, 'one-to-one')
        evaluated = [recovery(public, truth, WordMapping(job['forms'], c['assignments'])) for c in job['candidates']]
        reports.append({'id': job['id'], 'bundle': job['bundle'], 'profile': job['profile'],
            'selected_rank': selected, 'before': evaluated[0], 'after': evaluated[selected],
            'archive_oracle_exact_token_accuracy': max(r['exact_token_accuracy'] for r in evaluated),
            'candidates': len(scores)})
        scorer.cache.clear()  # Keep the memory bound per archive.
    deltas = [r['after']['exact_token_accuracy'] - r['before']['exact_token_accuracy'] for r in reports]
    report = {'manifest_sha256': manifest['sha256'], 'runs': reports,
        'summary': {'archives': len(reports), 'dictionaries': sum(r['candidates'] for r in reports),
            'improved': sum(d > 0 for d in deltas), 'worsened': sum(d < 0 for d in deltas),
            'unchanged': sum(d == 0 for d in deltas), 'mean_accuracy_change': mean(deltas),
            'mean_before': mean(r['before']['exact_token_accuracy'] for r in reports),
            'mean_after': mean(r['after']['exact_token_accuracy'] for r in reports)},
        'scope': 'development archives only; pooled overlaps bundles; pretrained Caesar exposure unknown; final test unscored'}
    if validate:
        if json.loads((out / 'report.json').read_text()) != report:
            raise ValueError('Report differs')
        write_json(out / 'validation.json', {'validated': True, 'manifest_sha256': manifest['sha256'], 'dictionaries': sum(r['candidates'] for r in reports), 'recomputed_masked_words': scorer.inference_rows})
    else:
        write_json(out / 'report.json', report)
    print(json.dumps(report['summary'], indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--model', type=Path, default=DEFAULT_MODEL)
    parser.add_argument('--out', type=Path, default=Path('experiments/results/word-mapping/neural-rerank'))
    parser.add_argument('--top', type=int, default=5)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    run(args.parent, args.model, args.out, top=args.top, resume=args.resume, validate=args.validate)
