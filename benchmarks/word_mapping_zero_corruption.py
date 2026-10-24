"""Start exactly at truth and compare strict ascent with normal annealing."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from benchmarks.word_mapping_widening import OUT as PARENT, PARENT as SOURCE, SEEDS, accuracy_subset, load_truth, prepare
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.oracle_mapping import OracleStartSearch
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.objective import objective_score

OUT = Path('experiments/results/word-mapping/zero-corruption-calibration')
POLICIES = ('greedy', 'annealing')


def resources(parent):
    parent = Path(parent)
    manifest = json.loads((parent / 'manifest.json').read_text())
    validation = json.loads((parent / 'validation.json').read_text())
    parent_report = json.loads((parent / 'report.json').read_text())
    if (digest(manifest['protocol']) != manifest['sha256'] or not validation['validated']
            or validation['manifest_sha256'] != manifest['sha256']
            or validation['report_sha256'] != digest(parent_report)):
        raise ValueError('Validated widening parent required')
    p = manifest['protocol']
    # Reconstruct foundation and keys instead of trusting mutable truth exports.
    model, morphology, candidates, publics, held, _, _ = prepare(SOURCE, parent,
        targets=tuple(p['targets']), holdout_tokens=p['holdout_tokens_requested'],
        steps=p['base_steps'], seeds=tuple(p['seeds']), restarts=p['restarts'], validate=True)
    truths = {target: load_truth(parent / f'truth/fit-{target}.json') for target in publics}
    held_truth = load_truth(parent / 'truth/holdout.json')
    return model, morphology, candidates, publics, truths, held, held_truth, manifest['sha256']


def snapshot(search, public, truth):
    search.scorer.validate()
    search.validate_oracle()
    current, best = search.scorer.mapping, search.best_mapping
    for mapping, expected in ((current, search.scorer.objective), (best, search.archive[0]['score'])):
        full = objective_score(search.model, public.segments, mapping, injective=True)
        if not math.isclose(full, expected, abs_tol=1e-7, rel_tol=1e-12):
            raise ValueError('Oracle trajectory full score mismatch')
    current_recovery = recovery(public, truth, current)
    if not math.isclose(current_recovery['exact_token_accuracy'], search.correct_tokens/search.total_tokens):
        raise ValueError('Oracle full recovery mismatch')
    return {'evaluations': search.evaluations, 'current_score': search.scorer.objective,
        'best_score': search.archive[0]['score'], 'current_recovery': current_recovery,
        'best_recovery': recovery(public, truth, best)}


def verify_witness(search, witness):
    if witness is None:
        return
    mapping = WordMapping(search.candidates.forms, {**search.gold, **witness['changes']})
    full_delta = objective_score(search.model, search.segments, mapping, injective=True)-search.initial_objective
    if not math.isclose(full_delta, witness['score_delta'], abs_tol=1e-7, rel_tol=1e-10):
        raise ValueError('Perfect-dictionary witness score mismatch')
    tokens = sum(search.word_counts[w] for w, f in mapping.assignments.items() if f == search.gold[w])
    if tokens-search.total_tokens != witness['token_delta']:
        raise ValueError('Perfect-dictionary witness recovery mismatch')


def run(parent=PARENT, out=OUT, *, steps=20000, seeds=SEEDS, validate=False):
    if type(steps) is not int or steps < 1:
        raise ValueError('Positive diagnostic budget required')
    parent, out = Path(parent), Path(out)
    model, morphology, candidates, publics, truths, held, held_truth, parent_sha = resources(parent)
    candidate = candidates['oracle']
    paths = [Path(__file__), Path('src/voynich_smt/oracle_mapping.py'),
             Path('src/voynich_smt/widening_mapping.py'), Path('src/voynich_smt/bootstrap_mapping.py'),
             Path('benchmarks/word_mapping_widening.py'),
             *sorted(Path('src/voynich_smt/word_mapping').glob('*.py'))]
    protocol = {'version': 1, 'parent_sha256': parent_sha, 'steps': steps, 'seeds': list(seeds),
        'policies': list(POLICIES), 'candidate_sha256': digest(asdict(candidate)),
        'truth_sha256': {str(k): digest(asdict(v)) for k, v in truths.items()},
        'initialization': 'perfect fit dictionary; zero corruptions; one start; no restarts',
        'objective': 'unchanged parent n-gram score; oracle recovery is measured, not optimized',
        'scope': 'explicit development oracle diagnostic; final test unscored',
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    path = out / 'manifest.json'
    if validate:
        if json.loads(path.read_text()) != manifest:
            raise ValueError('Oracle diagnostic protocol differs')
    else:
        if path.exists():
            raise ValueError('Output already exists')
        write_json(path, manifest)
    rows = []
    known_forms = set(candidates['training'].forms)
    for target, public in publics.items():
        truth = truths[target]
        for policy in POLICIES:
            for seed in seeds:
                config = SearchConfig(seed=seed, restarts=1, steps_per_restart=steps,
                    active_types=len(truth.decoding), initialization='frequency', injective=True, archive_size=1)
                search = OracleStartSearch(model, candidate, morphology, public, truth, config, policy=policy)
                trace = [snapshot(search, public, truth)]
                if trace[0]['current_recovery']['exact_token_accuracy'] != 1 or trace[0]['current_recovery']['exact_type_accuracy'] != 1:
                    raise ValueError('Initial dictionary is not perfect')
                for stop in sorted({1, 10, 100, 1000, 5000, steps}):
                    if stop > steps:
                        continue
                    search.advance(stop-search.evaluations)
                    trace.append(snapshot(search, public, truth))
                verify_witness(search, search.first_departure)
                verify_witness(search, search.perfect_score_witness)
                best = search.best_mapping
                best_held = accuracy_subset(held, held_truth, best, lambda w, f: w in search.gold)
                initial_mapping = WordMapping(candidate.forms, search.gold)
                initial_held = accuracy_subset(held, held_truth, initial_mapping, lambda w, f: w in search.gold)
                if initial_held['tokens'] and initial_held['accuracy'] != 1:
                    raise ValueError('Perfect fit mapping fails recurring holdout baseline')
                row = {'target': target, 'policy': policy, 'seed': seed, 'evaluations': search.evaluations,
                    'search_sha256': search.identity, 'initial_score': search.initial_objective,
                    'best_score_gain': search.archive[0]['score']-search.initial_objective,
                    'current_score_gain': search.scorer.objective-search.initial_objective,
                    'trace': trace, 'proposal_quality': search.quality, 'statistics': search.statistics,
                    'first_departure': search.first_departure, 'perfect_score_witness': search.perfect_score_witness,
                    'best_training_attested': accuracy_subset(public, truth, best, lambda w, f: f in known_forms),
                    'initial_holdout_recurring': initial_held, 'best_holdout_recurring': best_held,
                    'best_assignments': dict(best.assignments), 'current_assignments': dict(search.scorer.assignments)}
                directory = out / 'runs' / str(target) / policy / f'seed-{seed}'
                if validate:
                    if json.loads((directory / 'report.json').read_text()) != row:
                        raise ValueError('Replayed zero-corruption run differs')
                else:
                    write_json(directory / 'report.json', row)
                rows.append(row)
                print(f'{policy} {target} seed-{seed}: best recovery {100*trace[-1]["best_recovery"]["exact_token_accuracy"]:.2f}%, score gain {row["best_score_gain"]:.2f}', flush=True)
    summary = []
    for target in publics:
        for policy in POLICIES:
            selected = [r for r in rows if r['target'] == target and r['policy'] == policy]
            summary.append({'target': target, 'policy': policy, 'runs': len(selected), 'initial_token_accuracy': 1.0,
                'mean_best_token_accuracy': mean(r['trace'][-1]['best_recovery']['exact_token_accuracy'] for r in selected),
                'mean_current_token_accuracy': mean(r['trace'][-1]['current_recovery']['exact_token_accuracy'] for r in selected),
                'mean_best_type_accuracy': mean(r['trace'][-1]['best_recovery']['exact_type_accuracy'] for r in selected),
                'mean_best_training_attested_accuracy': mean(r['best_training_attested']['accuracy'] for r in selected),
                'mean_best_score_gain': mean(r['best_score_gain'] for r in selected),
                'mean_best_holdout_recurring_accuracy': mean(r['best_holdout_recurring']['accuracy'] for r in selected if r['best_holdout_recurring']['accuracy'] is not None) if any(r['best_holdout_recurring']['accuracy'] is not None for r in selected) else None,
                'strict_score_witness_runs': sum(r['perfect_score_witness'] is not None for r in selected),
                'accepted_score_up_recovery_down': sum(r['proposal_quality']['up/down']['accepted'] for r in selected)})
    report = {'manifest_sha256': manifest['sha256'], 'summary': summary,
        'run_sha256': {f'{r["target"]}/{r["policy"]}/{r["seed"]}': digest(r) for r in rows},
        'runs': len(rows), 'evaluations': sum(r['evaluations'] for r in rows)}
    if validate:
        if json.loads((out / 'report.json').read_text()) != report:
            raise ValueError('Replayed diagnostic summary differs')
        write_json(out / 'validation.json', {'validated': True, 'manifest_sha256': manifest['sha256'],
            'runs': report['runs'], 'evaluations': report['evaluations'], 'report_sha256': digest(report)})
    else:
        write_json(out / 'report.json', report)
    print(json.dumps(summary, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--steps', type=int, default=20000)
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    run(args.parent, args.out, steps=args.steps, validate=args.validate)
