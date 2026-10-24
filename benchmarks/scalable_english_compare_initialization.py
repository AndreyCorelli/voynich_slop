"""Evaluate a matched random/frequency initialization comparison."""
import argparse
import json
from pathlib import Path
from statistics import mean


def compare(random_root, frequency_root, output):
    roots = {'random': random_root, 'frequency': frequency_root}
    saved = {name: json.loads((root/'inference.json').read_text()) for name,root in roots.items()}
    normalized = []
    for name,inference in saved.items():
        protocol = json.loads(json.dumps(inference['protocol']))
        assert protocol['search'].pop('initialization', 'random') == name
        normalized.append(protocol)
        assert all(run['step'] == protocol['search']['proposals'] and run['stop_reason'] == 'proposal_limit'
                   for run in inference['runs']), 'Incomplete runs cannot support equal-proposal comparison'
        assert [r['seed'] for r in inference['runs']] == protocol['seeds']
    assert normalized[0] == normalized[1], 'Comparison changes more than initialization'
    methods = {}
    for name,root in roots.items():
        inference = saved[name]
        evaluation = json.loads((root/'evaluation.json').read_text())
        diagnostics = json.loads((root/'analysis/diagnostics.json').read_text())
        validation = json.loads((root/'analysis/validation.json').read_text())
        assert validation['status'] == 'validated'
        assert evaluation['cipher_sha256'] == diagnostics['cipher_sha256'] == inference['protocol']['cipher_sha256']
        evaluations = {r['seed']: r for r in evaluation['runs']}
        runs = []
        for run in inference['runs']:
            seed = run['seed']
            measured = evaluations[seed]
            method = diagnostics['methods'][f'seed-{seed}']
            attributed = diagnostics['attribution'][str(seed)]
            assert method['token_accuracy'] == measured['score_selected_best']['token_accuracy']
            runs.append({'seed': seed, 'steps': run['step'], 'elapsed_seconds': run['elapsed_seconds'],
                         'initial_token_accuracy': measured['initial']['token_accuracy'],
                         'initial_score': run['initial_score'], 'best_score': run['best_score'],
                         'token_accuracy': method['token_accuracy'], 'correct_types': method['correct_types'],
                         'type_accuracy': measured['score_selected_best']['type_accuracy'],
                         'frequency_bands': method['frequency_bands'],
                         'visited_types': attributed['visited_types'],
                         'ever_offered_true_types': sum(row['offered'] for row in attributed['rows']),
                         'failure_categories': attributed['categories']})
        methods[name] = {'runs': runs, 'mean_token_accuracy': mean(r['token_accuracy'] for r in runs),
                         'mean_initial_token_accuracy': mean(r['initial_token_accuracy'] for r in runs),
                         'mean_correct_types': mean(r['correct_types'] for r in runs),
                         'selected_seed': evaluation['selected_seed'],
                         'selected_token_accuracy': evaluation['selected_token_accuracy'],
                         'inventory_coverage': evaluation['inventory_coverage']}
    assert methods['random']['inventory_coverage'] == methods['frequency']['inventory_coverage']
    result = {'scope': 'Paired initialization comparison on one work-disjoint continuous literary prefix',
              'protocol_except_initialization': normalized[0], 'methods': methods,
              'paired_changes': [{'seed': a['seed'], 'token_accuracy_change': b['token_accuracy']-a['token_accuracy'],
                                  'correct_types_change': b['correct_types']-a['correct_types']}
                                 for a,b in zip(methods['random']['runs'], methods['frequency']['runs'])],
              'grammar': 'not_evaluated', 'semantics': 'not_evaluated',
              'limits': ['One older work and small source model; no generalization rate is established.',
                         'Frequency starts share one key; seeds vary subsequent search.',
                         'Source score selects keys independently of literal evaluation.',
                         'Missing forms remain in the denominator; million-form scale remains untested.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as handle:
        json.dump(result,handle,indent=2)
        handle.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--random', type=Path, required=True)
    parser.add_argument('--frequency', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.random,args.frequency,args.output)
    print(json.dumps({name:{k:v for k,v in values.items() if k not in ('runs','inventory_coverage')}
                      for name,values in report['methods'].items()},indent=2))
