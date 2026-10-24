from dataclasses import replace
import json
from pathlib import Path

import pytest

import benchmarks.german_free_prefix as benchmark
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.recovery import Recovery


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUTPUT', tmp_path/'checkpoint.json')
    monkeypatch.setattr(benchmark, 'ARTIFACTS', tmp_path/'inputs')
    return tmp_path


def test_prepare_only_preserves_science_and_selects_26(isolated, monkeypatch):
    monkeypatch.setattr(benchmark, 'recover_observed_codes', lambda request: pytest.fail('Unexpected solve'))
    report = benchmark.run(1000, prepare_only=True)
    assert report['boundary']['largest_verified_sat'] == 23
    assert report['boundary']['smallest_proved_unsat'] == 30
    assert report['next_input'].endswith('words-26.json')
    base = HiddenRecoveryRequest.from_dict(json.loads(benchmark.UNSAT.read_text())['request'])
    for count in range(24, 30):
        payload = json.loads((benchmark.ARTIFACTS/'budget-1000ms'/f'words-{count}.json').read_text())
        request = HiddenRecoveryRequest.from_dict(payload['request'])
        assert request.ciphertext.words == base.ciphertext.words[:count]
        assert replace(request, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) == base


def test_unknown_keeps_bounds_and_larger_budget_retries_same_prefix(isolated, monkeypatch):
    calls = []
    def solve(request):
        calls.append((len(request.ciphertext.words), request.timeout_ms))
        return Recovery('UNKNOWN', 0, reason_unknown='test timeout')
    monkeypatch.setattr(benchmark, 'recover_observed_codes', solve)
    report = benchmark.run(1000)
    assert calls == [(26, 1000)]
    assert report['boundary']['unresolved_sizes'] == list(range(24, 30))
    assert not report['complete']
    report = benchmark.run(2000, resume=True)
    assert calls == [(26, 1000), (26, 2000)]
    assert not report['boundary']['minimality_proven']
    cached = json.loads(benchmark.OUTPUT.read_text())
    cached['experiments'][-1]['input_sha256'] = 'tampered'
    benchmark.OUTPUT.write_text(json.dumps(cached))
    with pytest.raises(ValueError, match='mismatch'):
        benchmark.run(2000, resume=True)


def test_unsat_shrinks_bound_without_claiming_minimality(isolated, monkeypatch):
    calls = []
    def solve(request):
        calls.append(len(request.ciphertext.words))
        return Recovery('UNSAT' if len(calls) == 1 else 'UNKNOWN', 0)
    monkeypatch.setattr(benchmark, 'recover_observed_codes', solve)
    report = benchmark.run(1000)
    assert calls == [26, 24]
    assert report['boundary']['smallest_proved_unsat'] == 26
    assert report['boundary']['unresolved_sizes'] == [24, 25]
    assert not report['complete']
