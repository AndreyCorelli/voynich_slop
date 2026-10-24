"""Matched baseline, independent joint and training-phrase proposal searches."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import platform
from statistics import mean
import time

from benchmarks.word_mapping_ablation import load_truth
from benchmarks.word_mapping_recovery import public_input, resources
from benchmarks.word_mapping_neural_probe import PARENT
from voynich_smt.bootstrap_mapping import AgreementModel, BootstrapOptions, BootstrapSearch
from voynich_smt.phrase_mapping import PhraseSearch
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.objective import objective_score

OUT = Path('experiments/results/word-mapping/phrase-calibration')
BUNDLES = ('bundle-1', 'bundle-2', 'bundle-3')
ARMS = {
    'baseline': BootstrapOptions(),
    'joint': BootstrapOptions(joint_probability=.25),
    'phrase': BootstrapOptions(joint_probability=.25),
}

SEEDS = (101, 202)


def configuration(public, options, seed, steps):
    types = len({w for s in public.segments for w in s})
    return SearchConfig(seed=seed, restarts=3, steps_per_restart=steps,
        initialization='mixed', active_types=types, injective=True, archive_size=30,
        archive_min_distance=max(2, types // 10) if options.shortlist_probability else 1)


def prepare(parent, out, steps, *, resume=False, validate=False):
    if type(steps) is not int or steps < 1:
        raise ValueError('Positive steps required')
    parent_manifest = json.loads((parent / 'manifest.json').read_text())
    parent_validation = json.loads((parent / 'validation.json').read_text())
    if digest(parent_manifest['protocol']) != parent_manifest['sha256'] or not parent_validation['validated'] or parent_validation['manifest_sha256'] != parent_manifest['sha256']:
        raise ValueError('Validated parent required')
    model, morphology, candidates = resources(parent / 'bundle-1/foundation')
    if model.identity != parent_manifest['protocol']['model_sha256'] or digest(asdict(candidates)) != parent_manifest['protocol']['candidate_sha256'] or morphology.identity != parent_manifest['protocol']['morphology_sha256']:
        raise ValueError('Training resources changed')
    publics = {}
    for bundle in BUNDLES:
        study = parent / bundle / 'study'
        public = public_input(study / 'fixtures/one-to-one.json')
        if public.identity != json.loads((study / 'manifest.json').read_text())['protocol']['fixture_sha256']['one-to-one']:
            raise ValueError('Public fixture changed')
        publics[bundle] = public
    paths = [Path(__file__), Path('src/voynich_smt/phrase_mapping.py'), Path('src/voynich_smt/bootstrap_mapping.py'),
        Path('benchmarks/word_mapping_recovery.py'), Path('benchmarks/word_mapping_ablation.py'),
        *sorted(Path('src/voynich_smt/word_mapping').glob('*.py'))]
    protocol = {'version': 1, 'parent_sha256': parent_manifest['sha256'],
        'public_sha256': {b: p.identity for b, p in publics.items()},
        'model_sha256': model.identity, 'morphology_sha256': morphology.identity,
        'candidate_sha256': digest(asdict(candidates)), 'seeds': list(SEEDS),
        'arms': {name: asdict(options) for name, options in ARMS.items()},
        'configurations': {f'{b}/{name}/{seed}': asdict(configuration(p, options, seed, steps))
            for b, p in publics.items() for name, options in ARMS.items() for seed in SEEDS},
        'python': platform.python_version(), 'backend': 'python-reference',
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scope': 'three separate same-author development bundles; training-only attested pair proposals; same n-gram objective; no neural search; final test unscored'}
    protocol = json.loads(json.dumps(protocol))
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    if (out / 'manifest.json').exists():
        if not (resume or validate) or json.loads((out / 'manifest.json').read_text()) != manifest:
            raise ValueError('Output exists or protocol changed')
    elif validate:
        raise ValueError('Missing experiment')
    else:
        write_json(out / 'manifest.json', manifest)
    return model, morphology, candidates, publics, manifest


def search_phase(model, morphology, candidates, publics, out, manifest, steps, *, resume=False, validate=False):
    hashes = {}
    agreement = AgreementModel(morphology)
    for bundle, public in publics.items():
        for arm, options in ARMS.items():
            for seed in SEEDS:
                label = f'{bundle}/{arm}/seed-{seed}'
                directory = out / 'runs' / label
                config = configuration(public, options, seed, steps)
                search_class = PhraseSearch if arm == 'phrase' else BootstrapSearch
                search = search_class(model, candidates, morphology, public.segments, config, options, input_sha256=public.identity)
                if (directory / 'checkpoint.json').exists():
                    if not (resume or validate):
                        raise ValueError('Search exists')
                    search.resume(directory / 'checkpoint.json')
                elif validate:
                    raise ValueError('Missing checkpoint')
                if validate:
                    if not search.complete or search.evaluations != config.restarts * steps:
                        raise ValueError('Search incomplete')
                    archive = json.loads((directory / 'archive.json').read_text())
                    if digest(archive) != digest({'forms': list(candidates.forms), 'rows': search.archive}):
                        raise ValueError('Archive/checkpoint mismatch')
                    for row in archive['rows']:
                        mapping = WordMapping(candidates.forms, row['assignments'])
                        expected = objective_score(model, public.segments, mapping, injective=True) + options.agreement_weight * agreement.score(mapping.render(public.segments))
                        if not math.isclose(expected, row['score'], abs_tol=1e-8, rel_tol=1e-12):
                            raise ValueError('Archived bootstrap objective differs')
                    saved_hypotheses = json.loads((directory / 'hypotheses.json').read_text())
                    if saved_hypotheses != search.hypotheses():
                        raise ValueError('Saved hypothesis support differs')
                    saved = json.loads((directory / 'search-report.json').read_text())
                    if saved['search_sha256'] != search.identity or saved['evaluations'] != search.evaluations or saved['statistics'] != search.statistics:
                        raise ValueError('Saved search report differs')
                else:
                    if not search.complete:
                        started = time.perf_counter()
                        while not search.complete:
                            search.advance(steps)
                            search.checkpoint(directory / 'checkpoint.json')
                        seconds = time.perf_counter() - started
                    else:
                        existing = directory / 'search-report.json'
                        seconds = json.loads(existing.read_text())['seconds'] if existing.exists() else 0.0
                    # Complete checkpoints can regenerate derived exports after an interrupted write.
                    write_json(directory / 'archive.json', {'forms': list(candidates.forms), 'rows': search.archive})
                    write_json(directory / 'hypotheses.json', search.hypotheses())
                    write_json(directory / 'search-report.json', {'search_sha256': search.identity,
                        'evaluations': search.evaluations, 'statistics': search.statistics, 'seconds': seconds})
                    archive = json.loads((directory / 'archive.json').read_text())
                hashes[label] = digest(archive)
                print(f"{'Validated' if validate else 'Searched'} {label}", flush=True)
    report = {'manifest_sha256': manifest['sha256'], 'archives': hashes,
        'searches': len(hashes), 'restarts': len(hashes) * 3, 'mutations': len(hashes) * 3 * steps}
    if validate:
        if json.loads((out / 'search-report.json').read_text()) != report:
            raise ValueError('Search phase report differs')
    else:
        write_json(out / 'search-report.json', report)
    return report


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['arm']].append(row)
    summary = []
    baseline = {(r['bundle'], r['seed']): r['recovery']['exact_token_accuracy'] for r in rows if r['arm'] == 'baseline'}
    for arm, values in sorted(grouped.items()):
        delta = [r['recovery']['exact_token_accuracy'] - baseline[r['bundle'], r['seed']] for r in values]
        summary.append({'arm': arm, 'runs': len(values),
            'mean_exact_token_accuracy': mean(r['recovery']['exact_token_accuracy'] for r in values),
            'mean_exact_type_accuracy': mean(r['recovery']['exact_type_accuracy'] for r in values),
            'mean_archive_oracle_accuracy': mean(r['archive_oracle_accuracy'] for r in values),
            'mean_accuracy_change_from_baseline': mean(delta),
            'improved': sum(d > 0 for d in delta), 'worsened': sum(d < 0 for d in delta),
            'seconds': sum(r['seconds'] for r in values)})
    return summary


def evaluate(model, morphology, candidates, publics, parent, out, manifest):
    search_report = json.loads((out / 'search-report.json').read_text())
    if search_report['manifest_sha256'] != manifest['sha256']:
        raise ValueError('Search belongs to another protocol')
    agreement = AgreementModel(morphology)
    rows = []
    for bundle, public in publics.items():
        # Truth loaded only after all searches have finished, for evaluation.
        truth = load_truth(parent / bundle / 'study', 'one-to-one')
        gold = WordMapping(candidates.forms, {w: candidates.forms.index(form) for w, form in truth.decoding.items()})
        gold_grammar = agreement.score(gold.render(public.segments))
        gold_ngram = model.score(gold.render(public.segments)).log_likelihood
        for arm, options in ARMS.items():
            for seed in SEEDS:
                label = f'{bundle}/{arm}/seed-{seed}'
                directory = out / 'runs' / label
                archive = json.loads((directory / 'archive.json').read_text())
                if digest(archive) != search_report['archives'][label]:
                    raise ValueError('Archive changed before evaluation')
                evaluations = [recovery(public, truth, WordMapping(candidates.forms, r['assignments'])) for r in archive['rows']]
                mapping = WordMapping(candidates.forms, archive['rows'][0]['assignments'])
                best_grammar = agreement.score(mapping.render(public.segments))
                hypotheses = json.loads((directory / 'hypotheses.json').read_text())
                confidence = []
                for word, value in hypotheses.items():
                    majority = value['alternatives'][0]
                    confidence.append({'ciphertext': word, 'support': majority['archive_support'],
                        'correct': majority['surface'] == truth.decoding[word]})
                saved = json.loads((directory / 'search-report.json').read_text())
                rows.append({'bundle': bundle, 'arm': arm, 'seed': seed, 'archive_sha256': digest(archive),
                    'truth_sha256': digest(asdict(truth)), 'recovery': evaluations[0],
                    'archive_oracle_accuracy': max(e['exact_token_accuracy'] for e in evaluations),
                    'archive_dictionaries': len(archive['rows']), 'best_agreement': best_grammar,
                    'truth_agreement': gold_grammar, 'best_objective': archive['rows'][0]['score'],
                    'truth_objective': gold_ngram + options.agreement_weight * gold_grammar,
                    'support_evaluation': confidence, 'seconds': saved['seconds'], 'statistics': saved['statistics']})
    calibration = []
    for arm in ARMS:
        values = [v for r in rows if r['arm'] == arm for v in r['support_evaluation']]
        for low, high in ((0, .5), (.5, .75), (.75, .9), (.9, 1.00001)):
            selected = [v for v in values if low <= v['support'] < high]
            calibration.append({'arm': arm, 'support_low': low, 'support_high': min(high, 1),
                'assignments': len(selected), 'accuracy': mean(v['correct'] for v in selected) if selected else None})
    return {'manifest_sha256': manifest['sha256'], 'rows': rows, 'summary': summarize(rows),
        'support_calibration': calibration, 'scope': manifest['protocol']['scope'],
        'mutations': search_report['mutations']}


def run(parent=PARENT, out=OUT, *, steps=20000, resume=False, validate=False):
    parent, out = Path(parent), Path(out)
    model, morphology, candidates, publics, manifest = prepare(parent, out, steps, resume=resume, validate=validate)
    search_phase(model, morphology, candidates, publics, out, manifest, steps, resume=resume, validate=validate)
    report = evaluate(model, morphology, candidates, publics, parent, out, manifest)
    if validate:
        if json.loads((out / 'report.json').read_text()) != report:
            raise ValueError('Evaluation report differs')
        write_json(out / 'validation.json', {'validated': True, 'manifest_sha256': manifest['sha256'], 'searches': len(report['rows']), 'mutations': report['mutations']})
    else:
        write_json(out / 'report.json', report)
    print(json.dumps(report['summary'], indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--steps', type=int, default=20000)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    run(args.parent, args.out, steps=args.steps, resume=args.resume, validate=args.validate)
