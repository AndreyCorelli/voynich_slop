"""Verify distinct valid training explanations without further solver fits."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from benchmarks import latin_h2_compressed as comparison
from benchmarks import latin_compact_membership as compact
from voynich_smt.data.corpus import digest, write_json


def calculate():
    source = json.loads((comparison.OUT / 'prepared.json').read_text())
    assert json.loads((comparison.OUT / 'validation.json').read_text())['verified']
    for path, checksum in source['code_sha256'].items(): assert digest(Path(path).read_text()) == checksum
    rows = []
    for rung in source['rungs']:
        if rung['size'] != 32768: continue
        fixture = rung['fixtures'][0]; folder = comparison.OUT / rung['job'] / fixture['id']
        result = json.loads((folder / 'positive-result.json').read_text())
        if result['status'] != 'SAT': continue
        assert result['verified']
        metadata = fixture['inventory']
        assert hashlib.sha256(Path(metadata['path']).read_bytes()).hexdigest() == metadata['sha256']
        automaton = compact.load_automaton(fixture['case']['automaton'])
        truth = {code: letter for letter, codes in fixture['truth']['key'].items() for code in codes}
        recovered = result['recovered_key']
        decode = lambda key, words: [''.join(key[code] for code in word) for word in words]
        assert max(Counter(truth.values()).values()) <= fixture['max_homophones']
        assert max(Counter(recovered.values()).values()) <= fixture['max_homophones']
        actual = decode(truth, fixture['arms']['positive'])
        fitted = decode(recovered, fixture['arms']['positive'])
        assert actual == fixture['truth']['train'] and fitted == result['training_words']
        assert all(automaton.accepts(word) for word in actual + fitted)
        held = decode(recovered, fixture['held_cipher'])
        assert held == result['held_words']
        rows.append({'mode': rung['mode'], 'fixture_sha256': digest(fixture), 'result_sha256': digest(result),
                     'distinct_valid_training_explanations': any(truth[c] != letter for c, letter in recovered.items()),
                     'code_changes': [{'code': c, 'truth': truth[c], 'fitted': letter} for c, letter in sorted(recovered.items()) if truth[c] != letter],
                     'training_changes': [{'position': i+1, 'truth': t, 'fitted': w} for i,(t,w) in enumerate(zip(actual, fitted)) if t != w],
                     'held_truth': fixture['truth']['held'], 'held_first_key': held,
                     'training_exact': sum(x==y for x,y in zip(actual,fitted)),
                     'held_exact': sum(x==y for x,y in zip(fixture['truth']['held'],held))})
    return {'prepared_sha256': digest(source), 'analysis_code_sha256': digest(Path(__file__).read_text()), 'rows': rows,
            'scope': 'Generating key and first fitted key both satisfy frozen training membership/capacity. No new fit, alternative-key selection or score replacement.'}


if __name__ == '__main__':
    result = calculate(); path = comparison.OUT / 'ambiguity-analysis.json'
    if path.exists(): assert json.loads(path.read_text()) == result
    else: write_json(path, result)
    print('Verified training-explanation comparison for', len(result['rows']), 'SAT cases')
