"""Audit matched context/cipher preservation and compare first-key outcomes."""
from collections import Counter
import json
from pathlib import Path
from benchmarks import latin_h2_natural_context as experiment
from voynich_smt.data.corpus import digest, write_json


def calculate():
    p = experiment.prepare()
    report = json.loads((experiment.OUT/'report.json').read_text())
    assert report['complete'] and report['prepared_sha256'] == digest(p)
    source = experiment.prior.prepare()
    raw = json.loads(Path(source['source_path']).read_text())
    pairs = []
    for index, (short, long) in enumerate(zip(p['jobs'][::2], p['jobs'][1::2])):
        assert short['pair'] == long['pair'] == index+1
        assert short['full_held'] == long['full_held'] == source['passages'][index]['held']
        assert short['full_held_cipher'] == long['full_held_cipher']
        assert short['training_end_exclusive'] == long['training_end_exclusive']
        assert long['record_start'] == short['record_start']-48
        assert long['prefix_records'] == raw['records'][long['record_start']:short['record_start']]
        if short['fixture'] and long['fixture']:
            a, b = short['fixture'], long['fixture']
            assert a['inventory'] == b['inventory'] and a['case'] == b['case']
            assert a['truth']['key'] == b['truth']['key']
            assert a['arms']['positive'] == b['arms']['positive'][-48:]
            assert a['truth']['train'] == b['truth']['train'][-48:]
            # Independently check backward alternating prefix phase. Immediately
            # before the old code-0 start, the previous occurrence must be code 1.
            count = Counter()
            for word, cipher in zip(reversed(b['truth']['train'][:48]), reversed(b['arms']['positive'][:48])):
                for letter, code in zip(reversed(word), reversed(cipher)):
                    assert code == b['truth']['key'][letter][1-count[letter] % 2]
                    count[letter] += 1
        result = {'pair': index+1, 'adaptive': True, 'conditions': {}}
        for job in (short, long):
            row = next(r for r in report['conditions'] if r['job'] == job['job'])
            result['conditions'][str(job['training_length'])] = {
                'admitted': job['admitted'], 'covered_before_fit': None if job['covered_mask'] is None else sum(job['covered_mask']),
                'missing_training': job['coverage']['through-medieval-rare']['missing_training'],
                **{k: row[k] for k in ('status', 'reused', 'training_exact', 'holdout_scores', 'first_observed_key_exact', 'shuffle_status', 'alternative_status') if k in row}}
            if job['reuse']:
                for name, sha in job['reuse']['files'].items():
                    assert digest((Path(job['reuse']['folder'])/name).read_text()) == sha
                    assert (Path(job['reuse']['folder'])/name).read_bytes() == (experiment.OUT/job['job']/name).read_bytes()
        if short['fixture']:
            folder = experiment.OUT/short['job']
            alternative = json.loads((folder/'ambiguity-result.json').read_text())
            first = json.loads((folder/'positive-result.json').read_text())
            if alternative['status'] == 'SAT':
                altkey = alternative['alternative_key']
                diagnostic = {
                    'scope': 'Training-only diagnostic of returned alternative; no alternate heldout scoring or first-key replacement.',
                    'changed_codes': {c: {'first': v, 'alternative': altkey[c]} for c, v in first['recovered_key'].items() if altkey[c] != v},
                    'changed_training_words': [{'truth': truth, 'alternative': word} for truth, word in zip(short['fixture']['truth']['train'], alternative['training_words']) if truth != word]}
                if long['fixture']:
                    planted = {c: letter for letter, codes in long['fixture']['truth']['key'].items() for c in codes if c in long['observed_codes']}
                    combined = {**planted, **altkey}
                    diagnostic['long_context_capacity_with_new_codes_set_to_generating_values'] = dict(Counter(combined.values()))
                    diagnostic['long_context_capacity_exceeded_under_that_completion'] = max(Counter(combined.values()).values()) > 2
                    diagnostic['completion_scope'] = 'Truth-assisted explanatory completion, not a proof excluding every extension of the old alias.'
                result['short_alternative_diagnostic'] = diagnostic
        pairs.append(result)
    return {'prepared_sha256': digest(p), 'analysis_code_sha256': digest(Path(__file__).read_text()), 'pairs': pairs,
        'scope': 'Seven adaptive matched context comparisons. Identical original ciphers and holdouts; partial scores exclude unseen codes, never count them as wrong. Coverage failures retained; reused records explicitly marked. Overlapping contexts and repeated holdouts do not provide independent replication.'}


if __name__ == '__main__':
    experiment.validate(); result = calculate(); path = experiment.OUT/'analysis.json'
    if path.exists(): assert json.loads(path.read_text()) == result
    else: write_json(path, result)
    print(json.dumps(result, indent=2))
