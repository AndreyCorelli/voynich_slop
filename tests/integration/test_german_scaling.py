from dataclasses import asdict, replace
from itertools import product
import json
from pathlib import Path

import pytest

import benchmarks.german_scaling as scaling
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text


@pytest.mark.parametrize('minimum,maximum', [(1, 1), (1, 3), (2, 3)])
def test_length_certificates_against_enumerated_emission_lengths(minimum, maximum):
    request = HiddenRecoveryRequest(Text.from_string('x'), Alphabet(tuple('ab')),
        Alphabet(('x',)), Bounds('verbose', 2, minimum, maximum),
        WordDictionary.from_strings(('ab', 'aba')))
    feasible = {sum(lengths) for n in (2, 3)
                for lengths in product(range(minimum, maximum+1), repeat=n)}
    for size in range(1, 11):
        probe = replace(request, ciphertext=Text.from_string('x'*size))
        assert bool(scaling.length_obstructions(probe)) == (size not in feasible)


def test_preparation_certifies_boundary_and_keeps_controls_blind(tmp_path, monkeypatch):
    monkeypatch.setattr(scaling, 'ARTIFACTS', tmp_path/'artifacts')
    monkeypatch.setattr(scaling, 'OUTPUT', tmp_path/'report.json')
    report = scaling.run(1000)
    assert report['solver_calls'] == 0
    assert report['effective_sizes'] == [22, 23, 30, 40, 51]
    assert report['boundary']['minimality_proven']
    assert report['boundary']['smallest_proved_unsat'] == 23
    base = HiddenRecoveryRequest.from_dict(json.loads(scaling.BASELINE.read_text())['request'])
    for row in report['experiments']:
        payload = json.loads(Path(row['public_input']).read_text())
        assert digest(payload) == row['input_sha256']
        request = HiddenRecoveryRequest.from_dict(payload['request'])
        assert replace(request, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) == base
        assert request.ciphertext.words[:22] == base.ciphertext.words
        if row['word_count'] > 22:
            assert row['status'] == 'UNSAT_BY_LENGTH'
            assert row['length_obstructions'][0]['position'] == 23
            assert row['length_obstructions'][0]['ciphertext_word'] == 's'
    for seed in (7, 17):
        rows = [r for r in report['controls'] if r['seed'] == seed]
        largest = json.loads(Path(rows[-1]['public_input']).read_text())['request']['ciphertext']['words']
        key = None
        for row in rows:
            payload = json.loads(Path(row['public_input']).read_text())
            truth = json.loads(Path(row['truth_path']).read_text())
            assert set(payload) == {'request', 'codeword_domains'}
            assert digest(payload) == row['input_sha256']
            assert digest(truth) == row['truth_sha256']
            request = HiddenRecoveryRequest.from_dict(payload['request'])
            assert replace(request, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) == base
            assert payload['request']['ciphertext']['words'] == largest[:row['word_count']]
            assert key is None or truth['encoder'] == key
            key = truth['encoder']
            verify(request, {'status': 'SAT', 'verified': True, 'encoder': key,
                             'plaintext': truth['plaintext'], 'choices': truth['choices'], 'nulls': []})
            assert row['recovery_status'] == 'NOT_RUN'


def test_baseline_witness_is_checked_before_accepting_minimality(tmp_path, monkeypatch):
    baseline = json.loads(scaling.BASELINE.read_text())
    baseline['result']['verified'] = False
    path = tmp_path/'baseline.json'
    path.write_text(json.dumps(baseline))
    monkeypatch.setattr(scaling, 'BASELINE', path)
    with pytest.raises(RuntimeError, match='verification'):
        scaling.run()
