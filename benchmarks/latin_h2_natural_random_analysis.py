"""Independent audit of fresh natural cyclic/random comparison outcomes."""
from collections import Counter
from itertools import product
import json
from pathlib import Path
import random
from benchmarks import latin_h2_natural_random as experiment
from voynich_smt.data.corpus import digest, write_json


def calculate():
    p = experiment.prepare()
    report = json.loads((experiment.OUT/'report.json').read_text())
    assert report['complete'] and report['prepared_sha256'] == digest(p)
    source = experiment.context.prior.prepare()
    raw = json.loads(Path(source['source_path']).read_text())
    compact = experiment.context.prior.baseline.compact
    policies = json.loads((compact.OUT/'report.json').read_text())['modes']
    automata = {mode: compact.load_automaton(row['automaton']) for mode, row in policies.items()}
    start = max(block['record_end_exclusive'] for block in source['passages'])
    selected = experiment.context.prior.passages.select_passages(raw['records'], start, set(policies['through-medieval-rare']['alphabet']['symbols']), 7)
    assert selected == p['passages']
    pairs = []
    for i, block in enumerate(selected):
        coverage = {mode: {'missing_training': [w for w in block['train'] if not a.accepts(w)],
                          'missing_held': [w for w in block['held'] if not a.accepts(w)]} for mode, a in automata.items()}
        pair = {'pair': i+1, 'record_start': block['record_start'], 'record_end_exclusive': block['record_end_exclusive'],
                'missing_training': coverage['through-medieval-rare']['missing_training'],
                'missing_held': coverage['through-medieval-rare']['missing_held'],
                'novel_held_occurrences': sum(w not in block['train'] for w in block['held']), 'conditions': {}}
        for job in p['jobs'][2*i:2*i+2]:
            assert job['coverage'] == coverage
            f = job['fixture']; key = f['truth']['key']
            assert f['truth']['train'] == block['train']
            codes = [''.join(x) for x in product('qrstuvwx', repeat=2)]; random.Random(11201+i).shuffle(codes)
            assert key == {l: codes[2*j:2*j+2] for j, l in enumerate(policies['through-medieval-rare']['alphabet']['symbols'])}
            # Independently reproduce per-occurrence RNG streams, including held.
            rng = random.Random(11401+i); random_train = [[key[l][rng.randrange(2)] for l in word] for word in block['train']]
            rng = random.Random(11501+i); random_held = [[key[l][rng.randrange(2)] for l in word] for word in block['held']]
            assert random_held == job['full_held_cipher']
            if job['selection'] == 'iid-random': assert random_train == f['arms']['positive']
            seen = {c for word in f['arms']['positive'] for c in word}
            assert job['covered_mask'] == [set(word) <= seen for word in random_held]
            assert job['admitted'] == (not coverage['through-medieval-rare']['missing_training'])
            row = next(r for r in report['conditions'] if r['job'] == job['job'])
            result = {'status': row['status'], 'observed_codes': len(seen), 'covered_before_fit': sum(job['covered_mask']),
                      'training_code_histogram': dict(sorted(Counter(c for word in f['arms']['positive'] for c in word).items())),
                      **{k: row[k] for k in ('training_exact', 'holdout_scores', 'first_observed_key_exact', 'shuffle_status', 'alternative_status', 'timings') if k in row}}
            if job['admitted']:
                folder = experiment.OUT/job['job']; alt = json.loads((folder/'ambiguity-result.json').read_text())
                first = json.loads((folder/'positive-result.json').read_text())
                if first['status'] == 'SAT':
                    result['first_wrong_training'] = [{'truth': t, 'first': w} for t, w in zip(f['truth']['train'], first['training_words']) if t != w]
                if alt['status'] == 'SAT':
                    result['alternative_training_diagnostic'] = {
                        'changed_codes': {c: {'first': l, 'alternative': alt['alternative_key'][c]} for c, l in first['recovered_key'].items() if l != alt['alternative_key'][c]},
                        'changed_words': [{'truth': t, 'alternative': w} for t, w in zip(f['truth']['train'], alt['training_words']) if t != w],
                        'scope': 'Training-only diagnostic, no alternative heldout rescoring or first-key replacement.'}
            pair['conditions'][job['selection']] = result
        pairs.append(pair)
    return {'prepared_sha256': digest(p), 'analysis_code_sha256': digest(Path(__file__).read_text()), 'pairs': pairs,
            'scope': 'Seven fresh passages; random choices unbalanced and independent per occurrence. Shared random holdouts within each training-choice pair. Coverage-conditioned first-key accuracy; paired scores are not independent samples. Finite dictionary failures are not solver UNSAT; unknowns unevaluated.'}


if __name__ == '__main__':
    experiment.validate(); result = calculate(); path = experiment.OUT/'analysis.json'
    if path.exists(): assert json.loads(path.read_text()) == result
    else: write_json(path, result)
    print(json.dumps(result, indent=2))
