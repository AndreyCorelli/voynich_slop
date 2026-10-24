"""Evaluate likelihood-selected existing restarts without new inference."""
import argparse
import json
from pathlib import Path
from statistics import mean


def summarize(result):
    runs = result['runs']
    if not runs:
        raise ValueError('No completed restarts')
    reference = runs[0]['stages'][-1]
    for run in runs:
        stage = run['stages'][-1]
        if any(stage[k] != reference[k] for k in ('types', 'source', 'cipher_vocabulary')):
            raise ValueError('Restart source models or vocabularies differ')
    # Choose before consulting accuracy; seed ID is the deterministic tie break.
    selected = max(runs, key=lambda r: (r['stages'][-1]['log_likelihoods'][-1], -r['seed']))
    rows = [{'seed': r['seed'], 'log_likelihood': r['stages'][-1]['log_likelihoods'][-1],
             'token_accuracy': r['stages'][-1]['token_accuracy']} for r in runs]
    chosen = next(r for r in rows if r['seed'] == selected['seed'])
    return {'selection_rule': 'maximum final training log evidence, then lowest seed ID',
            'selected': chosen, 'mean_restart_accuracy': mean(r['token_accuracy'] for r in rows),
            'oracle_best_accuracy_diagnostic': max(r['token_accuracy'] for r in rows),
            'selected_matches_best_recovery': chosen['token_accuracy'] == max(r['token_accuracy'] for r in rows),
            'restarts': rows,
            'limitations': 'Reused development text and few search seeds. Selection uses training evidence, not cubed-channel Viterbi score. Truth is used only to evaluate the selected restart.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', nargs='+', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = {str(p): summarize(json.loads(p.read_text())) for p in args.results}
    rendered = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered)
