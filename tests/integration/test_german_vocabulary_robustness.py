from dataclasses import replace
import json

import pytest

import benchmarks.german_vocabulary_robustness as benchmark
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import Recovery


def test_regional_variant_changes_only_vocabulary_alphabet_and_budget():
    base = HiddenRecoveryRequest.from_dict(json.loads(benchmark.BASELINE.read_text())['request'])
    v = {'words': ['a', 'ä', 'aä'], 'alphabet': ['a', 'ä']}
    q = benchmark.regional_request(base, v, 1000)
    assert q.dictionary == WordDictionary.from_strings(('a', 'ä', 'aä'))
    assert q.plaintext_alphabet == Alphabet(('a', 'ä'))
    assert replace(q, dictionary=base.dictionary, plaintext_alphabet=base.plaintext_alphabet,
                   timeout_ms=base.timeout_ms) == base
    with pytest.raises(ValueError, match='19-word'):
        benchmark.regional_request(replace(base, ciphertext=Text(base.ciphertext.words[:18])), v, 1000)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    base = HiddenRecoveryRequest.from_dict(json.loads(benchmark.BASELINE.read_text())['request'])
    old = {'words': [''.join(w) for w in base.dictionary.words],
           'alphabet': list(base.plaintext_alphabet.symbols)}
    def vocabulary(n):
        if n == 143:return old
        words = ['ab', 'abc'] if n == 113 else ['a', 'ab', 'abc']
        return {'words': words, 'alphabet': list('abc'), 'vocabulary_size': len(words),
                'source': {'id': n}}
    monkeypatch.setattr(benchmark, 'build_vocabulary', vocabulary)
    monkeypatch.setattr(benchmark, 'RESULTS', tmp_path/'results')
    monkeypatch.setattr(benchmark, 'ARTIFACTS', tmp_path/'inputs')
    return tmp_path


def test_length_certificate_and_unknown_checkpoint_do_not_mix(isolated, monkeypatch):
    calls = []
    def solve(q):
        calls.append(q)
        return Recovery('UNKNOWN', 0)
    monkeypatch.setattr(benchmark, 'recover_observed_codes', solve)
    report = benchmark.run(1000, (113, 123))
    assert len(calls) == 1
    assert report['summary']['UNSAT_BY_LENGTH'] == [113]
    assert report['summary']['UNKNOWN'] == [123]
    assert not report['summary']['SAT'] and not report['summary']['UNSAT']
    assert report['experiments'][0]['length_obstructions'][0]['ciphertext_word'] == 's'
    assert not report['experiments'][0]['solver_run']
    benchmark.run(1000, (113, 123), resume=True)
    assert len(calls) == 1
    path = benchmark.RESULTS/'budget-1000ms.json'
    cached = json.loads(path.read_text());cached['experiments'][-1]['input_sha256'] = 'tampered'
    path.write_text(json.dumps(cached))
    with pytest.raises(ValueError, match='mismatch'):
        benchmark.run(1000, (113, 123), resume=True)


def test_new_budget_keeps_previous_requests_and_checkpoints(isolated, monkeypatch):
    monkeypatch.setattr(benchmark, 'recover_observed_codes', lambda q: Recovery('UNKNOWN', 0))
    benchmark.run(1000, (123,))
    old = (benchmark.ARTIFACTS/'budget-1000ms'/'inputs'/'123.json').read_bytes()
    benchmark.run(2000, (123,))
    assert (benchmark.ARTIFACTS/'budget-1000ms'/'inputs'/'123.json').read_bytes() == old
    assert (benchmark.RESULTS/'budget-1000ms.json').exists()
    assert (benchmark.RESULTS/'budget-2000ms.json').exists()


def test_prepare_only_never_solves(isolated, monkeypatch):
    monkeypatch.setattr(benchmark, 'recover_observed_codes', lambda q: pytest.fail('Unexpected solver call'))
    report = benchmark.run(1000, (113, 123), prepare_only=True)
    assert report['experiments'] == [] and not report['complete']


@pytest.mark.parametrize('numbers', [(143,), (123, 123), ()])
def test_invalid_sources_rejected(numbers):
    with pytest.raises(ValueError, match='source'):
        benchmark.run(1000, numbers)
