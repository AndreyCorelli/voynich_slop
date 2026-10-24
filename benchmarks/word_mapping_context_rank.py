"""Oracle-controlled neighbor quality versus true-word proposal rank."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import random
from statistics import mean
import time

from benchmarks.word_mapping_ablation import load_truth
from benchmarks.word_mapping_recovery import public_input, resources
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL, file_hashes
from benchmarks.word_mapping_neural_probe import PARENT
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.neural_scoring import WholeWordScorer

DECODED = Path('experiments/results/word-mapping/pool-size-calibration')
OUT = Path('experiments/results/word-mapping/context-rank')
FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)
METRICS = ('neural_word_normalized', 'neural_raw', 'ngram_objective', 'training_frequency')


def ranking(values, gold_index, tolerance=1e-4):
    if not values or not 0 <= gold_index < len(values) or any(not math.isfinite(v) for v in values):
        raise ValueError('Invalid finite ranking scores')
    gold = values[gold_index]
    better = sum(v > gold + tolerance for v in values)
    tied = sum(abs(v - gold) <= tolerance for v in values)
    return {'midrank': 1 + better + (tied - 1) / 2,
        'top1_credit': min(max(1 - better, 0), tied) / tied,
        'top5_credit': min(max(5 - better, 0), tied) / tied,
        'reciprocal_rank': mean(1 / (1 + better + i) for i in range(tied)),
        'ties_including_gold': tied}


def target_jobs(scorer, words, positions):
    """Mask every occurrence; each job scores one word's complete subword set."""
    if not positions or len(set(positions)) != len(positions) or any(type(i) is not int or not 0 <= i < len(words) for i in positions):
        raise ValueError('Invalid target positions')
    if any(not isinstance(w, str) or not w or any(c.isspace() for c in w) for w in words):
        raise ValueError('Invalid surface words')
    base = [scorer._job(words, i) for i in positions]
    all_positions = {p for _, places, _ in base for p in places}
    result = []
    for ids, places, labels in base:
        for p in all_positions:
            ids[p] = scorer.tokenizer.mask_token_id
        result.append((ids, places, labels))
    return result


def freeze(parent=PARENT, decoded=DECODED, *, targets=24):
    parent, decoded = Path(parent), Path(decoded)
    if type(targets) is not int or targets < 1:
        raise ValueError('Positive target sample required')
    sources = {}
    for label, root in (('parent', parent), ('decoded', decoded)):
        manifest = json.loads((root / 'manifest.json').read_text())
        validation = json.loads((root / 'validation.json').read_text())
        if digest(manifest['protocol']) != manifest['sha256'] or not validation['validated'] or validation['manifest_sha256'] != manifest['sha256']:
            raise ValueError('Validated frozen sources required')
        sources[label] = manifest['sha256']
    decoded_manifest = json.loads((decoded / 'manifest.json').read_text())
    decoded_report = json.loads((decoded / 'report.json').read_text())
    saved_selection = json.loads((decoded / 'selection.json').read_text())
    if decoded_manifest['protocol']['parent_sha256'] != sources['parent'] or digest(saved_selection) != decoded_report['selection_sha256'] or decoded_report['manifest_sha256'] != sources['decoded']:
        raise ValueError('Decoded source provenance differs')
    model, _, catalog = resources(parent / 'bundle-1/foundation')
    parent_protocol = json.loads((parent / 'manifest.json').read_text())['protocol']
    if model.identity != parent_protocol['model_sha256'] or digest(asdict(catalog)) != parent_protocol['candidate_sha256']:
        raise ValueError('Training resources changed')
    probes = []
    for bundle in ('bundle-1', 'bundle-2', 'bundle-3'):
        study = parent / bundle / 'study'
        public = public_input(study / 'fixtures/one-to-one.json')
        truth = load_truth(study, 'one-to-one')
        if truth.public_sha256 != public.identity or tuple(tuple(truth.decoding[w] for w in s) for s in public.segments) != truth.plaintext:
            raise ValueError('Truth/public mismatch')
        sources[f'{bundle}/public'] = public.identity
        sources[f'{bundle}/truth'] = digest(asdict(truth))
        job = next(j for j in saved_selection if j['bundle'] == bundle and j['size'] == len(catalog.forms))
        decoding = job['candidates'][0]['assignments']
        actual = {w: catalog.forms[i] for w, i in decoding.items()}
        keys = sorted(truth.decoding)
        if set(actual) != set(keys):
            raise ValueError('Saved dictionary domain differs')
        rng = random.Random(713)
        while True:
            wrong = dict(zip(keys, rng.sample(catalog.forms, len(keys)), strict=True))
            if all(wrong[w] != truth.decoding[w] for w in keys):
                break
        sampled = sorted(keys, key=lambda w: digest({'public': public.identity, 'target': w}))[:targets]
        for cipher in sampled:
            gold = truth.decoding[cipher]
            if gold not in catalog.form_counts:
                raise ValueError('Diagnostic requires full training coverage')
            alternative_rng = random.Random(int(digest({'public': public.identity, 'target': cipher, 'seed': 314})[:16], 16))
            # Fixed training-only list; gold appended solely for oracle rank measurement.
            fixed = list(catalog.forms[:16])
            remaining = [w for w in catalog.forms if w not in fixed]
            fixed += alternative_rng.sample(remaining, min(16, len(remaining)))
            candidates = list(dict.fromkeys([*fixed, gold]))
            neighbors = sorted((w for w in keys if w != cipher), key=lambda w: digest({'target': cipher, 'neighbor': w, 'seed': 2718}))
            affected = [i for i, s in enumerate(public.segments) if cipher in s]
            cipher_segments = [public.segments[i] for i in affected]
            positions = [[i for i, w in enumerate(s) if w == cipher] for s in cipher_segments]
            contexts = {}
            for fraction in FRACTIONS:
                restored = set(neighbors[:int(fraction * len(neighbors))])
                context = {w: truth.decoding[w] if w in restored else wrong[w] for w in keys}
                contexts[f'correct-{int(fraction * 100)}'] = context
            contexts['saved-decoding'] = actual
            cases = {}
            for label, context in contexts.items():
                other = [w for s in cipher_segments for w in s if w != cipher]
                cases[label] = {'segments': [[context[w] for w in s] for s in cipher_segments],
                    'neighbor_token_accuracy': sum(context[w] == truth.decoding[w] for w in other) / len(other) if other else None}
            probes.append({'id': digest({'bundle': bundle, 'public': public.identity, 'target': cipher}),
                'bundle': bundle, 'ciphertext': cipher, 'gold': gold, 'candidates': candidates,
                'gold_index': candidates.index(gold), 'gold_training_rank': catalog.forms.index(gold) + 1,
                'occurrences': sum(map(len, positions)), 'positions': positions, 'contexts': cases})
    return json.loads(json.dumps(probes)), sources, model, catalog


def score_probe(probe, scorer, model, catalog):
    result = {'id': probe['id'], 'bundle': probe['bundle'], 'contexts': {}}
    for context, case in probe['contexts'].items():
        all_jobs, counts, ngram, frequency = [], [], [], []
        for candidate in probe['candidates']:
            segments = [list(s) for s in case['segments']]
            jobs = []
            for segment, positions in zip(segments, probe['positions'], strict=True):
                for position in positions:
                    segment[position] = candidate
                jobs.extend(target_jobs(scorer, segment, positions))
            all_jobs.extend(jobs)
            counts.append(len(jobs))
            ngram.append(model.score(segments).log_likelihood)
            frequency.append(math.log(catalog.form_counts[candidate]))
        outputs = []
        for start in range(0, len(all_jobs), scorer.batch_size):
            outputs.extend(scorer._batch(all_jobs[start:start + scorer.batch_size]))
        raw, normalized, offset = [], [], 0
        for count in counts:
            values = outputs[offset:offset + count]
            raw.append(math.fsum(v for v, _ in values))
            normalized.append(math.fsum(v / n for v, n in values))
            offset += count
        scores = dict(zip(METRICS, (normalized, raw, ngram, frequency), strict=True))
        result['contexts'][context] = {'neighbor_token_accuracy': case['neighbor_token_accuracy'],
            'scores': scores, 'ranks': {metric: ranking(values, probe['gold_index']) for metric, values in scores.items()}}
    return result


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        for context, case in row['contexts'].items():
            for metric, rank in case['ranks'].items():
                groups[context, metric].append(rank)
    return [{'context': context, 'metric': metric, 'targets': len(ranks),
        'top1': mean(r['top1_credit'] for r in ranks), 'top5': mean(r['top5_credit'] for r in ranks),
        'mrr': mean(r['reciprocal_rank'] for r in ranks), 'mean_rank': mean(r['midrank'] for r in ranks)}
        for (context, metric), ranks in sorted(groups.items())]


def run(parent=PARENT, decoded=DECODED, model_path=DEFAULT_MODEL, out=OUT, *, targets=24, resume=False, validate=False):
    parent, decoded, model_path, out = map(Path, (parent, decoded, model_path, out))
    probes, sources, model, catalog = freeze(parent, decoded, targets=targets)
    asset = json.loads((model_path / 'manifest.json').read_text())
    if digest(asset['protocol']) != asset['sha256'] or file_hashes(model_path) != asset['protocol']['files_sha256']:
        raise ValueError('Pinned model assets changed')
    paths = [Path(__file__), Path('src/voynich_smt/neural_scoring.py'),
        Path('benchmarks/word_mapping_recovery.py'), Path('benchmarks/word_mapping_ablation.py'),
        *sorted(Path('src/voynich_smt/word_mapping').glob('*.py'))]
    protocol = {'version': 1, 'source_sha256': sources, 'probe_sha256': digest(probes),
        'model_sha256': asset['sha256'], 'targets_per_bundle': targets, 'contexts': list(probes[0]['contexts']),
        'alternatives': 'training top16 + seeded uniform16; append true word if absent; same list across contexts',
        'metric': 'target-only all-occurrence word mask; raw and mean-pieces-per-word; no spelling revealed',
        'corruption': 'seeded injective uniform training dictionary, all assignments wrong; nested neighbor-type correction',
        'ranking': '1e-4 tie tolerance; average rank and expected top-k/MRR under uniform tie breaking',
        'device': 'cpu', 'dtype': 'float32', 'threads': 4, 'batch_size': 16,
        'python': platform.python_version(),
        'packages': {n: importlib.metadata.version(n) for n in ('torch', 'transformers', 'tokenizers', 'safetensors')},
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scope': 'oracle development diagnostic; truth controls context and gold inclusion; synthetic mixtures may collide; not recovery/search; pretrained exposure unknown; final test unscored'}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    if (out / 'manifest.json').exists():
        if not (resume or validate) or json.loads((out / 'manifest.json').read_text()) != manifest:
            raise ValueError('Output exists or protocol changed')
    elif validate:
        raise ValueError('Missing experiment')
    else:
        write_json(out / 'manifest.json', manifest)
        write_json(out / 'probes.json', probes)
    if json.loads((out / 'probes.json').read_text()) != probes:
        raise ValueError('Probe selection changed')
    scorer = WholeWordScorer.load(model_path / 'inference', batch_size=16, threads=4)
    rows = []
    for index, probe in enumerate(probes):
        path = out / 'rows' / f"{probe['id']}.json"
        saved = json.loads(path.read_text()) if path.exists() else None
        if saved and digest(saved['row']) != saved['sha256']:
            raise ValueError('Row checksum differs')
        if saved and resume and not validate:
            row = saved['row']
        else:
            start = time.perf_counter()
            before = scorer.inference_rows
            row = score_probe(probe, scorer, model, catalog)
            row['seconds'] = time.perf_counter() - start
            row['masked_word_jobs'] = scorer.inference_rows - before
            if validate:
                if not saved or any(row[k] != saved['row'][k] for k in ('id', 'bundle', 'masked_word_jobs')):
                    raise ValueError('Row identity/count differs')
                for context, case in row['contexts'].items():
                    reference = saved['row']['contexts'][context]
                    if case['neighbor_token_accuracy'] != reference['neighbor_token_accuracy']:
                        raise ValueError('Context accuracy differs')
                    for metric, values in case['scores'].items():
                        if len(values) != len(reference['scores'][metric]) or any(not math.isclose(v, r, abs_tol=1e-4, rel_tol=1e-6) for v, r in zip(values, reference['scores'][metric], strict=True)):
                            raise ValueError('Offline score recomputation differs')
                        if reference['ranks'][metric] != ranking(reference['scores'][metric], probe['gold_index']):
                            raise ValueError('Saved ranking differs')
                row = saved['row']
            else:
                write_json(path, {'row': row, 'sha256': digest(row)})
        if row['id'] != probe['id'] or row['bundle'] != probe['bundle']:
            raise ValueError('Row belongs to another probe')
        rows.append(row)
        if (index + 1) % 6 == 0 or index + 1 == len(probes):
            print(f"{'Validated' if validate else 'Scored'} {index + 1}/{len(probes)} context targets", flush=True)
    report = {'manifest_sha256': manifest['sha256'], 'probes': len(probes), 'summary': summarize(rows),
        'by_bundle': {b: summarize([r for r in rows if r['bundle'] == b]) for b in sorted({r['bundle'] for r in rows})},
        'scoring_seconds': sum(r['seconds'] for r in rows), 'masked_word_jobs': sum(r['masked_word_jobs'] for r in rows),
        'scope': protocol['scope']}
    if validate:
        if json.loads((out / 'report.json').read_text()) != report:
            raise ValueError('Summary differs')
        write_json(out / 'validation.json', {'validated': True, 'manifest_sha256': manifest['sha256'], 'probes': len(probes), 'recomputed_masked_word_jobs': scorer.inference_rows})
    else:
        write_json(out / 'report.json', report)
    print(json.dumps(report['summary'], indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--decoded', type=Path, default=DECODED)
    parser.add_argument('--model', type=Path, default=DEFAULT_MODEL)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--targets', type=int, default=24)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    run(args.parent, args.decoded, args.model, args.out, targets=args.targets, resume=args.resume, validate=args.validate)
