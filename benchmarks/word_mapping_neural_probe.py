"""Frozen counterexample comparison: offline Latin RoBERTa vs short context."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
import platform
from pathlib import Path
from statistics import mean

from benchmarks.word_mapping_ablation import load_truth
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL, file_hashes
from benchmarks.word_mapping_recovery import public_input
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.neural_scoring import WholeWordScorer

PARENT = Path('experiments/results/word-mapping/long-context-calibration')
METRICS = ('word_masked_log_sum', 'word_normalized_log_sum')
CONTEXTS = {'full-segment': None, 'radius-2': 2}


def freeze_probes(parent=PARENT, *, top=10):
    parent = Path(parent)
    if type(top) is not int or top < 1:
        raise ValueError('top must be positive')
    validation = json.loads((parent / 'validation.json').read_text())
    parent_manifest = json.loads((parent / 'manifest.json').read_text())
    if digest(parent_manifest['protocol']) != parent_manifest['sha256']:
        raise ValueError('Parent manifest checksum changed')
    if not validation['validated'] or validation['manifest_sha256'] != parent_manifest['sha256']:
        raise ValueError('Probe requires the validated frozen development experiment')
    probes, sources = [], {}
    for name in ('bundle-1', 'bundle-2', 'bundle-3', 'pooled'):
        study = parent / name / 'study'
        public = public_input(study / 'fixtures/one-to-one.json')
        truth = load_truth(study, 'one-to-one')
        if truth.public_sha256 != public.identity:
            raise ValueError('Truth/public identities differ')
        sources[f'{name}/public'] = public.identity
        sources[f'{name}/truth'] = digest(asdict(truth))
        seen = {}
        for profile in ('mixture', 'trigram'):
            path = parent / name / f'neighborhood-{profile}.json'
            saved = json.loads(path.read_text())
            audit = saved['report']
            if digest(audit) != saved['sha256'] or audit['public_sha256'] != public.identity:
                raise ValueError('Saved neighborhood changed')
            sources[f'{name}/{profile}'] = saved['sha256']
            for kind in ('injective_replacement', 'swap'):
                for rank, example in enumerate(audit['examples'][kind][:top]):
                    if example['objective_delta'] <= 1e-8:
                        continue
                    changes = {r['ciphertext']: r['after'] for r in example['changes']}
                    for row in example['changes']:
                        if truth.decoding[row['ciphertext']] != row['before']:
                            raise ValueError('Counterexample does not start from truth')
                    key = digest(changes)
                    provenance = {'ngram': profile, 'kind': kind, 'rank': rank,
                                  'ngram_delta': example['objective_delta']}
                    if key in seen:
                        seen[key]['selected_by'].append(provenance)
                        continue
                    wrong = tuple(tuple(changes.get(w, truth.decoding[w]) for w in s) for s in public.segments)
                    affected = [i for i, (a, b) in enumerate(zip(truth.plaintext, wrong)) if a != b]
                    if not affected:
                        raise ValueError('Counterexample changes no observed tokens')
                    decoding = {**truth.decoding, **changes}
                    if len(set(decoding.values())) != len(decoding):
                        raise ValueError('Selected probe violates the declared one-to-one constraint')
                    probe = {'id': digest({'bundle': name, 'changes': changes}), 'bundle': name,
                        'kind': kind, 'changes': changes, 'selected_by': [provenance],
                        'affected_segment_ids': affected,
                        'truth_segments': [truth.plaintext[i] for i in affected],
                        'wrong_segments': [wrong[i] for i in affected]}
                    seen[key] = probe
        probes.extend(seen.values())
    return json.loads(json.dumps(probes)), sources


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        for context in CONTEXTS:
            for metric in METRICS:
                delta = row['scores'][context]['delta'][metric]
                groups[context, metric].append(delta)
    report = []
    for (context, metric), deltas in sorted(groups.items()):
        report.append({'context': context, 'metric': metric, 'probes': len(deltas),
            'truth_preferred': sum(d < -1e-4 for d in deltas),
            'wrong_preferred': sum(d > 1e-4 for d in deltas),
            'tied': sum(abs(d) <= 1e-4 for d in deltas), 'mean_wrong_minus_truth': mean(deltas)})
    paired = []
    for metric in METRICS:
        full = [r['scores']['full-segment']['delta'][metric] for r in rows]
        local = [r['scores']['radius-2']['delta'][metric] for r in rows]
        paired.append({'metric': metric,
            'short_wrong_full_truth': sum(a > 1e-4 and b < -1e-4 for a, b in zip(local, full)),
            'short_truth_full_wrong': sum(a < -1e-4 and b > 1e-4 for a, b in zip(local, full)),
            'mean_full_minus_short_gap': mean(a - b for a, b in zip(full, local))})
    return {'summaries': report, 'paired_context_changes': paired,
        'by_bundle': dict(Counter(r['bundle'] for r in rows)),
        'scope': 'selected strongest ngram counterexamples; pretrained Caesar exposure unknown; no optimization or test scoring'}


def run(parent, model_path, out, *, top=10, batch_size=16, threads=4, resume=False, validate=False):
    parent, model_path, out = Path(parent), Path(model_path), Path(out)
    probes, sources = freeze_probes(parent, top=top)
    if not probes:
        raise ValueError('No improving frozen counterexamples selected')
    asset = json.loads((model_path / 'manifest.json').read_text())
    if digest(asset['protocol']) != asset['sha256'] or file_hashes(model_path) != asset['protocol']['files_sha256']:
        raise ValueError('Pinned model assets changed')
    code = [Path(__file__), Path('benchmarks/word_mapping_neural_model.py'),
            Path('src/voynich_smt/neural_scoring.py')]
    protocol = {'version': 1, 'source_sha256': sources, 'probe_sha256': digest(probes),
        'model_sha256': asset['sha256'], 'top_per_origin_kind': top,
        'contexts': CONTEXTS, 'batch_size': batch_size, 'threads': threads, 'device': 'cpu', 'dtype': 'float32',
        'python': platform.python_version(),
        'packages': {name: importlib.metadata.version(name) for name in ('torch', 'transformers', 'tokenizers', 'safetensors')},
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in code},
        'score': 'all pieces of each target word masked together; sum log marginals; also mean pieces per word',
        'validation_tolerance': {'absolute': 1e-4, 'relative': 1e-6}}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    if (out / 'manifest.json').exists():
        saved = json.loads((out / 'manifest.json').read_text())
        if not (resume or validate) or saved != manifest:
            raise ValueError('Probe output exists or model/protocol/code changed')
    elif validate:
        raise ValueError('Cannot validate a missing probe experiment')
    else:
        write_json(out / 'manifest.json', manifest)
        write_json(out / 'probes.json', probes)
    if json.loads((out / 'probes.json').read_text()) != probes:
        raise ValueError('Saved probe selection changed')
    scorer = WholeWordScorer.load(model_path / 'inference', batch_size=batch_size, threads=threads)
    rows = []
    for index, probe in enumerate(probes):
        path = out / 'rows' / f'{probe["id"]}.json'
        saved = json.loads(path.read_text()) if path.exists() else None
        if saved and digest(saved['row']) != saved['sha256']:
            raise ValueError('Probe row checksum changed')
        if saved and resume and not validate:
            row = saved['row']
        else:
            row = {'id': probe['id'], 'bundle': probe['bundle'], 'kind': probe['kind'], 'scores': {}}
            for context, radius in CONTEXTS.items():
                true = scorer.score(probe['truth_segments'], context_radius=radius)
                wrong = scorer.score(probe['wrong_segments'], context_radius=radius)
                if true['words'] != wrong['words']:
                    raise ValueError('Compared dictionaries change the number of surface words')
                row['scores'][context] = {'truth': true, 'wrong': wrong,
                    'delta': {metric: wrong[metric] - true[metric] for metric in METRICS},
                    'subword_count_change': wrong['subwords'] - true['subwords']}
            if validate:
                if saved is None:
                    raise ValueError('Probe evaluation incomplete')
                reference = saved['row']
                if any(reference[k] != row[k] for k in ('id', 'bundle', 'kind')):
                    raise ValueError('Probe row identity changed')
                for context in CONTEXTS:
                    if reference['scores'][context]['subword_count_change'] != row['scores'][context]['subword_count_change']:
                        raise ValueError('Probe tokenization count changed')
                    for side in ('truth', 'wrong', 'delta'):
                        for metric, value in row['scores'][context][side].items():
                            if not math.isclose(value, reference['scores'][context][side][metric], abs_tol=1e-4, rel_tol=1e-6):
                                raise ValueError('Neural score differs from offline recomputation')
                row = reference
            else:
                write_json(path, {'row': row, 'sha256': digest(row)})
        rows.append(row)
        if (index + 1) % 5 == 0 or index + 1 == len(probes):
            print(f'{"Validated" if validate else "Scored"} {index + 1}/{len(probes)} neural probes', flush=True)
    report = {'manifest_sha256': manifest['sha256'], 'probes': len(probes), **summarize(rows)}
    if validate:
        if json.loads((out / 'report.json').read_text()) != report:
            raise ValueError('Saved probe summary differs from reconstruction')
        write_json(out / 'validation.json', {'validated': True, 'probes': len(probes),
            'manifest_sha256': manifest['sha256'], 'recomputed_masked_words': scorer.inference_rows})
    else:
        write_json(out / 'report.json', report)
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--model', type=Path, default=DEFAULT_MODEL)
    parser.add_argument('--out', type=Path, default=Path('experiments/results/word-mapping/neural-probe'))
    parser.add_argument('--top', type=int, default=10)
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    run(args.parent, args.model, args.out, top=args.top, batch_size=args.batch_size,
        threads=args.threads, resume=args.resume, validate=args.validate)
