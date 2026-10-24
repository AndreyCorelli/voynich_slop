"""Check a nested fixed-vocabulary length comparison and report common-prefix recovery."""
import argparse
import json
from pathlib import Path
from statistics import mean


def compare(short, long):
    a = json.loads((short / 'result.json').read_text())
    b = json.loads((long / 'result.json').read_text())
    protocols = []
    for value in (a, b):
        protocol = dict(value['protocol'])
        protocol.pop('requested_tokens')
        protocol.pop('reference_run', None)
        for key, default in [('initialization', 'random'), ('freeze', True), ('frequency_strength', .5),
                             ('warm_start', False), ('exploration', .05)]:
            protocol.setdefault(key, default)
        protocols.append(protocol)
    assert protocols[0] == protocols[1], 'Unexpected protocol differences'
    ap = json.loads((short / 'public.json').read_text())
    bp = json.loads((long / 'public.json').read_text())
    assert ap['training'] == bp['training']
    assert bp['ciphertext'][:len(ap['ciphertext'])] == ap['ciphertext']
    assert a['cipher_tokens'] == b['prefix_tokens']
    assert [r['seed'] for r in a['runs']] == [r['seed'] for r in b['runs']]
    rows = []
    for x, y in zip(a['runs'], b['runs']):
        assert len(x['stages']) == len(y['stages'])
        for s, t in zip(x['stages'], y['stages']):
            assert s['source'] == t['source']
            assert s['cipher_vocabulary'] == t['cipher_vocabulary']
        s, t = x['stages'][-1], y['stages'][-1]
        rows.append({'seed': x['seed'], 'short_accuracy': s['token_accuracy'],
                     'long_common_prefix_accuracy': t['prefix_token_accuracy'],
                     'long_full_accuracy': t['token_accuracy'],
                     'common_prefix_change_pp': 100 * (t['prefix_token_accuracy'] - s['token_accuracy'])})
    return {'short_tokens': a['cipher_tokens'], 'long_tokens': b['cipher_tokens'],
            'short_seconds': a['elapsed_seconds'], 'long_seconds': b['elapsed_seconds'],
            'mean_short_accuracy': mean(r['short_accuracy'] for r in rows),
            'mean_long_prefix_accuracy': mean(r['long_common_prefix_accuracy'] for r in rows),
            'mean_long_full_accuracy': mean(r['long_full_accuracy'] for r in rows), 'runs': rows,
            'limitation': 'Nested reused development text; active cipher vocabulary is deliberately fixed to the short run.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('short', type=Path)
    parser.add_argument('long', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = compare(args.short, args.long)
    rendered = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered)
