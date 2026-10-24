"""Compare paired English runs differing in one declared experimental factor."""
import argparse
import json
from pathlib import Path
from statistics import mean


def compare(before, after, *, vary='max_iterations'):
    old = json.loads((before / 'result.json').read_text())
    new = json.loads((after / 'result.json').read_text())
    if old['public_sha256'] != new['public_sha256']:
        raise ValueError('Public inputs differ')
    left, right = dict(old['protocol']), dict(new['protocol'])
    if vary not in {'max_iterations', 'initialization', 'freeze', 'warm_start', 'smoothing'}:
        raise ValueError('Unsupported comparison factor')
    for protocol in (left, right):
        protocol.setdefault('warm_start', False)
        protocol.setdefault('exploration', 0.05)
        protocol.setdefault('initialization', 'random')
        protocol.setdefault('freeze', True)
        protocol.setdefault('frequency_strength', 0.5)
        protocol.pop(vary)
    if left != right:
        raise ValueError('Protocols differ beyond declared comparison factor')
    if [r['seed'] for r in old['runs']] != [r['seed'] for r in new['runs']]:
        raise ValueError('Completed search seeds differ')
    rows = []
    for a, b in zip(old['runs'], new['runs']):
        if len(a['stages']) != len(b['stages']):
            raise ValueError('Completed stages differ')
        for x, y in zip(a['stages'], b['stages']):
            keys = ('types', 'cipher_vocabulary', 'candidate_token_ceiling')
            if vary != 'smoothing':
                keys += ('source',)
            elif any(x['source'][k] != y['source'][k] for k in ('vocabulary', 'counts')):
                raise ValueError('Smoothing comparison changes source vocabulary/counts')
            if any(x[k] != y[k] for k in keys):
                raise ValueError('Stage inputs differ')
            rows.append({'seed': a['seed'], 'types': x['types'],
                         'before_accuracy': x['token_accuracy'], 'after_accuracy': y['token_accuracy'],
                         'accuracy_change_pp': 100 * (y['token_accuracy'] - x['token_accuracy']),
                         'before_updates': len(x['log_likelihoods']) - 1,
                         'after_updates': len(y['log_likelihoods']) - 1,
                         'before_converged': x['converged'], 'after_converged': y['converged'],
                         'before_likelihood': x['log_likelihoods'][-1],
                         'after_likelihood': y['log_likelihoods'][-1],
                         'before_frozen': len(x['frozen']), 'after_frozen': len(y['frozen']),
                         'before_inconsistent_types': x['inconsistent_cipher_types'],
                         'after_inconsistent_types': y['inconsistent_cipher_types']})
    final_types = old['runs'][0]['stages'][-1]['types']
    finals = [r for r in rows if r['types'] == final_types]
    return {'vary': vary, 'before_setting': old['protocol'].get(vary, {'initialization': 'random', 'freeze': True, 'warm_start': False}.get(vary)),
            'after_setting': new['protocol'].get(vary), 'before_iteration_cap': old['protocol']['max_iterations'],
            'after_iteration_cap': new['protocol']['max_iterations'],
            'public_sha256': old['public_sha256'], 'stage_comparisons': rows,
            'before_mean_final_accuracy': mean(r['before_accuracy'] for r in finals),
            'after_mean_final_accuracy': mean(r['after_accuracy'] for r in finals),
            'before_seconds': old['elapsed_seconds'], 'after_seconds': new['elapsed_seconds'],
            'runtime_ratio': new['elapsed_seconds'] / old['elapsed_seconds'],
            'frequency_accuracy': old['frequency']['token_accuracy'],
            'interpretation': ('Longer earlier stages can change frozen constraints in later stages; this is a full-schedule comparison.'
                               if vary == 'max_iterations' else
                               'One declared factor changes across the full schedule; downstream frozen pairs may change. Fresh no-freeze and revisable warm-start are distinct carryover policies.')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--vary', choices=['max_iterations', 'initialization', 'freeze', 'warm_start', 'smoothing'], default='max_iterations')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = compare(args.before, args.after, vary=args.vary)
    rendered = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered)
