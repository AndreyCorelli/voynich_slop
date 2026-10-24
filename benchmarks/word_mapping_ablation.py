"""Development-only, paired multi-seed objective/search diagnostics."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import platform
from statistics import mean, stdev

from benchmarks.word_mapping_recovery import optimize, public_input, resources
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.annealing import Annealer, SearchConfig
from voynich_smt.word_mapping.controls import make_control
from voynich_smt.word_mapping.corpora import WordStream, validate_splits
from voynich_smt.word_mapping.diagnostics import truth_diagnostic
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.fixtures import CipherInput, CipherTruth, generate
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.morphology import MorphologyCatalog, WhitakerAnnotator
from voynich_smt.word_mapping.ngram import NgramModel
from voynich_smt.word_mapping.objective import objective_score, frequency_penalty


@dataclass(frozen=True)
class AblationPlan:
    seeds: tuple[int, ...] = (11, 22, 33)
    budgets: tuple[int, ...] = (10000, 100000)
    restarts: int = 1
    active_types: int = 100
    archive_size: int = 100
    fixture_kinds: tuple[str, ...] = ('one-to-one', 'homophonic')
    fixture_seed: int = 713
    control_seed: int = 314
    collapse_weights: tuple[float, ...] = (1.0, 5.0)
    controls: tuple[str, ...] = ()
    arm_names: tuple[str, ...] = ()
    control_arm_names: tuple[str, ...] = ()
    all_types_active: bool = False
    frequency_weights: tuple[float, ...] = ()
    constraint_arms: bool = False

    def __post_init__(self):
        if (not self.seeds or len(set(self.seeds)) != len(self.seeds) or
                any(type(seed) is not int for seed in self.seeds)):
            raise ValueError('Search seeds must be distinct integers')
        if (len(self.budgets) < 2 or tuple(sorted(set(self.budgets))) != tuple(self.budgets)
                or any(type(b) is not int or b < 1 for b in self.budgets)):
            raise ValueError('At least two increasing positive budgets required')
        for name in ('restarts', 'active_types', 'archive_size'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f'{name} must be positive')
        if (not self.fixture_kinds or len(set(self.fixture_kinds)) != len(self.fixture_kinds)
                or not set(self.fixture_kinds) <= {'one-to-one', 'homophonic', 'frequency-distorting', 'lossy'}):
            raise ValueError('Invalid or repeated fixture kind')
        if (len(set(self.controls)) != len(self.controls) or not set(self.controls) <= {
                'within-segment-shuffle', 'position-shuffle', 'bigram-surrogate'}):
            raise ValueError('Invalid or repeated control kind')
        if (len(set(self.collapse_weights)) != len(self.collapse_weights) or
                not all(math.isfinite(w) and w > 0 for w in self.collapse_weights)):
            raise ValueError('Collapse ablations must have distinct finite positive weights')
        if type(self.all_types_active) is not bool:
            raise ValueError('all_types_active must be Boolean')
        if type(self.constraint_arms) is not bool:
            raise ValueError('constraint_arms must be Boolean')
        if (len(set(self.frequency_weights)) != len(self.frequency_weights) or
                not all(math.isfinite(w) and w > 0 for w in self.frequency_weights)):
            raise ValueError('Frequency weights must be distinct finite positive values')
        if len(set(self.arm_names)) != len(self.arm_names) or len(set(self.control_arm_names)) != len(self.control_arm_names):
            raise ValueError('Repeated selected arms')
        selected = {arm['name'] for arm in self.arms()}
        if not set(self.control_arm_names) <= selected:
            raise ValueError('Control arms must be selected search arms')

    def arms(self):
        # One change at a time against baseline; this is not a factorial grid.
        arms = [{'name': 'baseline', 'model': 'mixture', 'initialization': 'frequency', 'collapse_weight': 0.0}]
        arms.extend({'name': name, 'model': name, 'initialization': 'frequency', 'collapse_weight': 0.0}
                    for name in ('unigram', 'bigram', 'trigram'))
        arms.extend({'name': f'{name}-init', 'model': 'mixture', 'initialization': name, 'collapse_weight': 0.0}
                    for name in ('random', 'lemma-aware'))
        arms.extend({'name': f'collapse-{weight:g}', 'model': 'mixture',
                     'initialization': 'frequency', 'collapse_weight': weight} for weight in self.collapse_weights)
        arms.extend({'name': f'frequency-{weight:g}', 'model': 'mixture',
                     'initialization': 'frequency', 'collapse_weight': 0.0,
                     'frequency_weight': weight} for weight in self.frequency_weights)
        if self.constraint_arms:
            arms.append({'name': 'injective', 'model': 'mixture', 'initialization': 'frequency',
                         'collapse_weight': 0.0, 'injective': True})
            arms.extend({'name': f'injective-frequency-{weight:g}', 'model': 'mixture',
                         'initialization': 'frequency', 'collapse_weight': 0.0,
                         'injective': True, 'frequency_weight': weight} for weight in self.frequency_weights)
        if len({arm['name'] for arm in arms}) != len(arms):
            raise ValueError('Collapse weights produce duplicate arm names')
        if self.arm_names:
            if not set(self.arm_names) <= {arm['name'] for arm in arms}:
                raise ValueError('Unknown selected arm')
            arms = [arm for arm in arms if arm['name'] in self.arm_names]
        return arms

    def jobs(self):
        return [{'fixture': fixture, 'arm': arm, 'seed': seed, 'budget': budget, 'control': control}
                for fixture in self.fixture_kinds for arm in self.arms()
                for seed in self.seeds for budget in self.budgets
                for control in ('original', *(self.controls if not self.control_arm_names
                    or arm['name'] in self.control_arm_names else ()))
                if not arm.get('injective', False) or fixture == 'one-to-one']


def search_config(plan, job, public=None):
    if plan.all_types_active and public is None:
        raise ValueError('All-types search requires public ciphertext')
    active_types = len({w for s in public.segments for w in s}) if plan.all_types_active else plan.active_types
    return SearchConfig(seed=job['seed'], restarts=plan.restarts, steps_per_restart=job['budget'],
        active_types=active_types, archive_size=plan.archive_size,
        initialization=job['arm']['initialization'], collapse_weight=job['arm']['collapse_weight'],
        frequency_weight=job['arm'].get('frequency_weight', 0.0),
        injective=job['arm'].get('injective', False))


def job_directory(out, job):
    return Path(out) / 'runs' / job['fixture'] / job['arm']['name'] / f'seed-{job["seed"]}' / f'budget-{job["budget"]}' / job['control']


def prepare(foundation, out, plan, *, resume=False, write=True):
    foundation, out = Path(foundation), Path(out)
    base, morphology, candidates = resources(foundation)
    streams = {name: WordStream.load(foundation / f'splits/{name}.json')
               for name in ('train', 'development', 'test')}
    split_hashes = validate_splits(streams)
    # The test split is read for overlap auditing only; not scored or optimized.
    train, development = streams['train'], streams['development']
    if not development.segments():
        raise ValueError('Empty development split')
    profiles = {'mixture': (0.0, 0.5, 0.5), 'unigram': (1.0, 0.0, 0.0),
                'bigram': (0.0, 1.0, 0.0), 'trigram': (0.0, 0.0, 1.0)}
    models = {name: NgramModel.train(train.segments(), replace(base.config,
        unigram_weight=u, bigram_weight=b, trigram_weight=t), training_sha256=train.identity)
        for name, (u, b, t) in profiles.items()}
    fixtures, truths = {}, {}
    for kind in plan.fixture_kinds:
        fixtures[kind], truths[kind] = generate(development.segments(), seed=plan.fixture_seed,
            kind=kind, source={'source_id': 'latin-development', 'stream_sha256': development.identity})
    annotator = WhitakerAnnotator(Path('data/vendor/whitakers-words'), mode=morphology.resource['mode'])
    if annotator.resource != morphology.resource:
        raise ValueError('Foundation morphology resource changed')
    evaluation_catalog = annotator.catalog(set(candidates.forms) | {
        w for s in development.segments() for w in s}, training_sha256=development.identity)
    source_files = [Path(__file__), Path('benchmarks/word_mapping_recovery.py'), Path('benchmarks/word_mapping_foundation.py'),
                    *sorted(Path('benchmarks').glob('word_mapping_parallel.py')),
                    *sorted(Path('benchmarks').glob('word_mapping_full_coverage.py')),
                    *sorted(Path('benchmarks').glob('word_mapping_objective_refinement.py')),
                    *sorted(Path('benchmarks').glob('word_mapping_long_context.py')),
                    *sorted(Path('src/voynich_smt/word_mapping').glob('*.py'))]
    protocol = {'version': 1, 'plan': asdict(plan), 'arms': plan.arms(),
        'foundation': str(foundation.resolve()), 'splits': split_hashes,
        'model_sha256': {name: model.identity for name, model in models.items()},
        'candidates_sha256': digest(asdict(candidates)), 'morphology_sha256': morphology.identity,
        'fixture_sha256': {kind: public.identity for kind, public in fixtures.items()},
        'evaluation_morphology_sha256': evaluation_catalog.identity,
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        'python': platform.python_version(),
        'scope': 'development only; no thresholds tuned or final-test search/scoring',
        'budget_semantics': 'evaluations per restart; independent runs, temperature schedule scaled to each budget',
        'control_semantics': 'fixed control seed, independently refitted with identical per-arm budgets'}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    if (out / 'manifest.json').exists():
        if not resume:
            raise ValueError('Ablation output exists; use --resume or a new --out directory')
        saved = json.loads((out / 'manifest.json').read_text())
        if saved != json.loads(json.dumps(manifest)):
            raise ValueError('Ablation inputs/config/code changed')
    if write:
        write_json(out / 'manifest.json', manifest)
        write_json(out / 'plan.json', {'jobs': plan.jobs(),
            'total_evaluations': sum(plan.restarts * job['budget'] for job in plan.jobs())})
        for name, model in models.items():
            model.save(out / f'models/{name}.json')
        write_json(out / 'candidates.json', asdict(candidates))
        for kind, public in fixtures.items():
            write_json(out / f'fixtures/{kind}.json', asdict(public))
            write_json(out / f'truth/{kind}.json', asdict(truths[kind]))
        evaluation_catalog.save(out / 'truth/morphology-evaluation.json')
    # Return public inputs only. Truth is loaded through the evaluation path.
    return manifest, models, candidates, fixtures, evaluation_catalog


def load_truth(out, kind):
    value = json.loads((Path(out) / f'truth/{kind}.json').read_text())
    return CipherTruth(value['public_sha256'], tuple(tuple(s) for s in value['plaintext']),
                       value['decoding'], value['deterministic_accuracy_ceiling'])


def job_public(fixtures, plan, job):
    public = fixtures[job['fixture']]
    if job['control'] == 'original':
        return public
    segments, audit = make_control(public.segments, kind=job['control'], seed=plan.control_seed)
    return CipherInput(segments, {'parent_public_sha256': public.identity}, audit)


def evaluate(out, model, candidates, public, search, catalog, job):
    mapping = search.best_mapping
    score = model.score(mapping.render(public.segments))
    result = {'job': job, 'public_sha256': public.identity, 'search_sha256': search.identity,
        'evaluations': search.evaluations, 'best_objective': search.archive[0]['score'],
        'score': asdict(score), 'collapse_penalty': mapping.collapse_penalty,
        'distinct_surface_forms': len({form for form in mapping.assignments.values() if form is not None}),
        'statistics': search.statistics, 'recovery': None, 'frequency_baseline': None,
        'truth_diagnostic': None, 'control_audit': None}
    if search.config.frequency_weight:
        result['frequency_penalty'] = frequency_penalty(model, public.segments, mapping)
    if job['control'] == 'original':
        truth = load_truth(out, job['fixture'])
        result['recovery'] = recovery(public, truth, mapping, morphology=catalog)
        frequency = candidates.initialize(public.segments, active_types=search.config.active_types,
                                          seed=0, mode='frequency')
        result['frequency_baseline'] = recovery(public, truth, frequency, morphology=catalog)
        result['truth_diagnostic'] = truth_diagnostic(model, candidates, public, truth, search.archive,
                                                     collapse_weight=search.config.collapse_weight,
                                                     frequency_weight=search.config.frequency_weight,
                                                     injective=search.config.injective)
    else:
        # Shuffled words no longer align with original plaintext; don't report
        # invalid recovery metrics or compare them to a fabricated true key.
        result['control_audit'] = public.encoder
    return result


def describe(values):
    return {'n': len(values), 'mean': mean(values), 'sd': stdev(values) if len(values) > 1 else None,
            'minimum': min(values), 'maximum': max(values)}


def summarize(rows):
    groups = defaultdict(list)
    paired = defaultdict(dict)
    diagnoses = Counter()
    for row in rows:
        job = row['job']
        groups[job['fixture'], job['arm']['name'], job['control'], job['budget']].append(row)
        paired[job['fixture'], job['arm']['name'], job['control'], job['seed']][job['budget']] = row
        if row['truth_diagnostic']:
            diagnostic = row['truth_diagnostic']
            diagnoses[(diagnostic['comparison_scope'], diagnostic['diagnosis'])] += 1
    summaries = []
    for (fixture, arm, control, budget), values in sorted(groups.items()):
        summary = {'fixture': fixture, 'arm': arm, 'control': control, 'budget_per_restart': budget,
            'fitness': describe([row['best_objective'] for row in values]),
            'collapse_penalty': describe([row['collapse_penalty'] for row in values]),
            'coverage': describe([row['score']['covered_tokens'] / row['score']['total_tokens'] for row in values]),
            'prediction_events': describe([row['score']['prediction_events'] for row in values])}
        if control == 'original':
            summary['exact_token_accuracy'] = describe([row['recovery']['exact_token_accuracy'] for row in values])
            summary['lemma_token_accuracy'] = describe([row['recovery']['lemma_token_accuracy'] for row in values
                if row['recovery']['lemma_token_accuracy'] is not None]) if any(
                row['recovery']['lemma_token_accuracy'] is not None for row in values) else None
            summary['truth_diagnoses'] = dict(Counter(row['truth_diagnostic']['diagnosis'] for row in values))
            summary['active_truth_feasible'] = all(row['truth_diagnostic']['active_truth_feasible'] for row in values)
            summary['candidate_constrained_token_accuracy_ceiling'] = describe([
                row['truth_diagnostic']['candidate_constrained_token_accuracy_ceiling'] for row in values])
        summaries.append(summary)
    differences = defaultdict(list)
    for (fixture, arm, control, seed), budgets in sorted(paired.items()):
        ordered = sorted(budgets)
        for low, high in zip(ordered, ordered[1:]):
            short, long = budgets[low], budgets[high]
            difference = {'seed': seed, 'fitness_change': long['best_objective'] - short['best_objective'],
                          'exact_token_accuracy_change': None}
            if control == 'original':
                difference['exact_token_accuracy_change'] = long['recovery']['exact_token_accuracy'] - short['recovery']['exact_token_accuracy']
            differences[fixture, arm, control, low, high].append(difference)
    budget_comparisons = []
    for (fixture, arm, control, low, high), values in sorted(differences.items()):
        comparison = {'fixture': fixture, 'arm': arm, 'control': control,
            'smaller_budget': low, 'larger_budget': high, 'paired_seeds': values,
            'fitness_change': describe([v['fitness_change'] for v in values])}
        if control == 'original':
            deltas = [v['exact_token_accuracy_change'] for v in values]
            comparison.update(exact_token_accuracy_change=describe(deltas),
                seeds_improving=sum(d > 0 for d in deltas), seeds_worsening=sum(d < 0 for d in deltas),
                seeds_unchanged=sum(d == 0 for d in deltas))
        budget_comparisons.append(comparison)
    return {'completed_runs': len(rows), 'total_evaluations': sum(r['evaluations'] for r in rows),
        'summaries': summaries, 'paired_budget_comparisons': budget_comparisons,
        'diagnoses': [{'scope': scope, 'diagnosis': diagnosis, 'runs': count}
                      for (scope, diagnosis), count in sorted(diagnoses.items())],
        'interpretation': 'Descriptive development results. Raw fitness is not comparable across scorer profiles; '
            'partial-domain oracle evidence is not a complete-dictionary diagnosis. No final-test or long-run gate is passed automatically.'}


def run(foundation, out, plan, *, resume=False):
    out = Path(out)
    manifest, models, candidates, fixtures, catalog = prepare(foundation, out, plan, resume=resume)
    rows = []
    jobs = plan.jobs()
    for index, job in enumerate(jobs):
        directory = job_directory(out, job)
        public = job_public(fixtures, plan, job)
        model = models[job['arm']['model']]
        config = search_config(plan, job, public)
        path = directory / 'result.json'
        if path.exists() and resume:
            saved = json.loads(path.read_text())
            row = saved['row']
            if digest(row) != saved['sha256'] or row['job'] != job:
                raise ValueError('Saved ablation result changed')
            search = Annealer(model, candidates, public.segments, config,
                              input_sha256=public.identity).resume(directory / 'checkpoint.json')
            if not search.complete or row['search_sha256'] != search.identity:
                raise ValueError('Saved run does not match checkpoint')
        else:
            search, timing = optimize(model, candidates, public, config, directory, resume=resume)
            row = evaluate(out, model, candidates, public, search, catalog, job)
            row['elapsed_seconds_this_invocation'] = timing['elapsed_seconds_this_invocation']
            row['evaluations_per_second'] = timing['evaluations_per_second']
            write_json(path, {'row': row, 'sha256': digest(row)})
        rows.append(row)
        if (index + 1) % 12 == 0 or index + 1 == len(jobs):
            print(f'Completed {index + 1}/{len(jobs)} ablation runs', flush=True)
    report = {'manifest_sha256': manifest['sha256'], **summarize(rows)}
    write_json(out / 'report.json', report)
    return report


def validate(out):
    out = Path(out)
    manifest = json.loads((out / 'manifest.json').read_text())
    if digest(manifest['protocol']) != manifest['sha256']:
        raise ValueError('Ablation manifest checksum mismatch')
    plan = AblationPlan(**manifest['protocol']['plan'])
    expected, models, candidates, fixtures, catalog = prepare(
        manifest['protocol']['foundation'], out, plan, resume=True, write=False)
    expected_plan = {'jobs': plan.jobs(), 'total_evaluations': sum(
        plan.restarts * job['budget'] for job in plan.jobs())}
    if digest(json.loads((out / 'plan.json').read_text())) != digest(expected_plan):
        raise ValueError('Saved ablation plan changed')
    if digest(json.loads((out / 'candidates.json').read_text())) != digest(asdict(candidates)):
        raise ValueError('Saved ablation candidate catalog changed')
    development = WordStream.load(Path(manifest['protocol']['foundation']) / 'splits/development.json')
    for name, model in models.items():
        if NgramModel.load(out / f'models/{name}.json').identity != model.identity:
            raise ValueError('Saved ablation model differs from training reconstruction')
    for kind, public in fixtures.items():
        if public_input(out / f'fixtures/{kind}.json') != public:
            raise ValueError('Ablation fixture changed')
        _, regenerated_truth = generate(development.segments(), seed=plan.fixture_seed,
            kind=kind, source={'source_id': 'latin-development', 'stream_sha256': development.identity})
        if load_truth(out, kind) != regenerated_truth:
            raise ValueError('Ablation truth differs from independent fixture reconstruction')
    if MorphologyCatalog.load(out / 'truth/morphology-evaluation.json').identity != catalog.identity:
        raise ValueError('Evaluation morphology changed')
    rows = []
    for job in plan.jobs():
        directory = job_directory(out, job)
        public = job_public(fixtures, plan, job)
        model = models[job['arm']['model']]
        config = search_config(plan, job, public)
        search = Annealer(model, candidates, public.segments, config,
                          input_sha256=public.identity).resume(directory / 'checkpoint.json')
        if not search.complete or search.evaluations != plan.restarts * job['budget']:
            raise ValueError('Ablation budget incomplete')
        archive = json.loads((directory / 'archive.json').read_text())
        if digest(archive) != digest({'forms': list(candidates.forms), 'rows': search.archive}):
            raise ValueError('Ablation archive differs from checkpoint')
        for archived in search.archive:
            mapping = WordMapping(candidates.forms, archived['assignments'])
            objective = objective_score(model, public.segments, mapping,
                collapse_weight=config.collapse_weight, frequency_weight=config.frequency_weight,
                injective=config.injective)
            if not math.isclose(objective, archived['score'], abs_tol=1e-8, rel_tol=1e-12):
                raise ValueError('Archived objective differs from full recomputation')
        saved = json.loads((directory / 'result.json').read_text())
        row = saved['row']
        if digest(row) != saved['sha256']:
            raise ValueError('Ablation row checksum mismatch')
        evaluated = evaluate(out, model, candidates, public, search, catalog, job)
        if any(row[k] != v for k, v in evaluated.items()):
            raise ValueError('Ablation metrics differ from independent recomputation')
        rows.append(row)
    report = json.loads((out / 'report.json').read_text())
    if digest(report) != digest({'manifest_sha256': expected['sha256'], **summarize(rows)}):
        raise ValueError('Ablation summary differs from paired run reconstruction')
    result = {'validated': True, 'runs': len(rows), 'total_evaluations': report['total_evaluations'],
              'manifest_sha256': manifest['sha256']}
    write_json(out / 'validation.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--foundation', type=Path, default=Path('experiments/results/word-mapping/foundation'))
    parser.add_argument('--out', type=Path, default=Path('experiments/results/word-mapping/ablation-development'))
    parser.add_argument('--seeds', type=int, nargs='+', default=[11, 22, 33])
    parser.add_argument('--budgets', type=int, nargs='+', default=[10000, 100000])
    parser.add_argument('--restarts', type=int, default=1)
    parser.add_argument('--active-types', type=int, default=100)
    parser.add_argument('--archive-size', type=int, default=100)
    parser.add_argument('--kinds', nargs='+', default=['one-to-one', 'homophonic'])
    parser.add_argument('--collapse-weights', type=float, nargs='*', default=[1.0, 5.0])
    parser.add_argument('--fixture-seed', type=int, default=713)
    parser.add_argument('--controls', action='store_true')
    parser.add_argument('--arms', nargs='*', default=[])
    parser.add_argument('--all-types', action='store_true')
    parser.add_argument('--frequency-weights', type=float, nargs='*', default=[])
    parser.add_argument('--constraints', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--plan', action='store_true', help='Print run count and budget without running')
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate(args.out), indent=2))
        return
    plan = AblationPlan(seeds=tuple(args.seeds), budgets=tuple(args.budgets), restarts=args.restarts,
        active_types=args.active_types, archive_size=args.archive_size, fixture_kinds=tuple(args.kinds),
        collapse_weights=tuple(args.collapse_weights), fixture_seed=args.fixture_seed,
        arm_names=tuple(args.arms), all_types_active=args.all_types,
        frequency_weights=tuple(args.frequency_weights), constraint_arms=args.constraints,
        controls=('within-segment-shuffle', 'position-shuffle', 'bigram-surrogate') if args.controls else ())
    if args.plan:
        print(json.dumps({'arms': plan.arms(), 'runs': len(plan.jobs()),
            'total_evaluations': sum(plan.restarts * job['budget'] for job in plan.jobs())}, indent=2))
        return
    report = run(args.foundation, args.out, plan, resume=args.resume)
    print(json.dumps({k: report[k] for k in ('completed_runs', 'total_evaluations', 'diagnoses')}, indent=2))


if __name__ == '__main__':
    main()
