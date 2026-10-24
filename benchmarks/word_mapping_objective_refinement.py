"""Paired training-only frequency and declared one-to-one constraint refinements."""
import argparse
import json
from pathlib import Path

from benchmarks.word_mapping_ablation import AblationPlan, validate
from benchmarks.word_mapping_parallel import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--foundation', type=Path, default=Path(
        'experiments/results/word-mapping/full-coverage-large/foundation'))
    parser.add_argument('--out', type=Path, default=Path(
        'experiments/results/word-mapping/objective-refinement'))
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate(args.out), indent=2))
        return
    plan = AblationPlan(seeds=(11, 22, 33, 44, 55), budgets=(10000, 50000), restarts=2,
        fixture_kinds=('one-to-one', 'homophonic'), all_types_active=True,
        frequency_weights=(1.0, 5.0), constraint_arms=True,
        arm_names=('baseline', 'frequency-1', 'frequency-5', 'injective', 'injective-frequency-1'),
        controls=('position-shuffle',), control_arm_names=('baseline',))
    if args.plan:
        print(json.dumps({'runs': len(plan.jobs()), 'total_evaluations': sum(
            plan.restarts * j['budget'] for j in plan.jobs()), 'arms': plan.arms()}, indent=2))
        return
    report = run(args.foundation, args.out, plan, workers=args.workers, resume=args.resume)
    print(json.dumps({k: report[k] for k in ('completed_runs', 'total_evaluations', 'diagnoses')}, indent=2))


if __name__ == '__main__':
    main()
