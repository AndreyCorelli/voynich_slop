"""Compare matched scheduling experiments after separate truth-based evaluation."""
import argparse
import json
from pathlib import Path
from statistics import mean


def compare(mixed, coverage, output):
    roots = {'mixed': mixed, 'coverage_first': coverage}
    inference = {name: json.loads((root/'inference.json').read_text()) for name, root in roots.items()}
    normalized = []
    for name, saved in inference.items():
        protocol = json.loads(json.dumps(saved['protocol']))
        assert protocol['search'].pop('scheduler') == name
        normalized.append(protocol)
        assert all(r['step'] == protocol['search']['proposals'] and r['stop_reason'] == 'proposal_limit'
                   for r in saved['runs']), 'Incomplete runs cannot support an equal-proposal comparison'
    assert normalized[0] == normalized[1], 'Comparison changes more than the scheduling policy'
    reports = {}
    for name, root in roots.items():
        evaluation = json.loads((root/'evaluation.json').read_text())
        diagnostics = json.loads((root/'analysis/diagnostics.json').read_text())
        assert json.loads((root/'analysis/validation.json').read_text())['status'] == 'validated'
        runs = []
        for run in inference[name]['runs']:
            seed = run['seed']
            method = diagnostics['methods'][f'seed-{seed}']
            attribution = diagnostics['attribution'][str(seed)]
            rows = attribution['rows']
            runs.append({'seed': seed, 'steps': run['step'], 'elapsed_seconds': run['elapsed_seconds'],
                         'best_score': run['best_score'], 'token_accuracy': method['token_accuracy'],
                         'correct_types': method['correct_types'], 'visited_types': attribution['visited_types'],
                         'ever_offered_true_types': sum(row['offered'] for row in rows),
                         'ever_active_true_types': sum(row['active'] for row in rows),
                         'frequency_bands': method['frequency_bands'], 'failure_categories': attribution['categories']})
        reports[name] = {'runs': runs, 'selected_seed': evaluation['selected_seed'],
                         'selected_token_accuracy': evaluation['selected_token_accuracy'],
                         'mean_token_accuracy': mean(r['token_accuracy'] for r in runs),
                         'mean_correct_types': mean(r['correct_types'] for r in runs),
                         'mean_visited_types': mean(r['visited_types'] for r in runs),
                         'mean_ever_offered_true_types': mean(r['ever_offered_true_types'] for r in runs)}
    deltas = [{'seed': a['seed'], 'token_accuracy_change': b['token_accuracy']-a['token_accuracy'],
               'correct_types_change': b['correct_types']-a['correct_types'],
               'visited_types_change': b['visited_types']-a['visited_types'],
               'ever_offered_true_types_change': b['ever_offered_true_types']-a['ever_offered_true_types']}
              for a,b in zip(reports['mixed']['runs'], reports['coverage_first']['runs'])]
    assert all(a['seed'] == b['seed'] for a,b in zip(reports['mixed']['runs'], reports['coverage_first']['runs']))
    result = {'scope': 'Matched scheduling comparison on training-overlapping engineering fixture',
              'protocol_except_scheduler': normalized[0], 'methods': reports, 'paired_changes': deltas,
              'grammar': 'not_evaluated', 'semantics': 'not_evaluated',
              'limitations': ['Three paired seeds on one fixture; no independent generalization estimate.',
                              'Scheduling changes which types receive early high-temperature proposals.',
                              'Visitation and offered candidates do not guarantee recovery.',
                              'Million-form inventory remains untested.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mixed', type=Path, required=True)
    parser.add_argument('--coverage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.mixed, args.coverage, args.output)
    print(json.dumps({k: {p:v[p] for p in ('mean_token_accuracy', 'mean_correct_types', 'mean_visited_types', 'mean_ever_offered_true_types')}
                      for k,v in result['methods'].items()}, indent=2))
