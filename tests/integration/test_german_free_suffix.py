from dataclasses import replace
import json

import pytest

import benchmarks.german_free_suffix as benchmark
from benchmarks.l3_conflict import verify
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.recovery import Recovery


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUTPUT', tmp_path/'checkpoint.json')
    monkeypatch.setattr(benchmark, 'ARTIFACTS', tmp_path/'inputs')


def test_prepare_first_deletion_and_empty_lower_certificate(isolated, monkeypatch):
    monkeypatch.setattr(benchmark, 'recover_observed_codes', lambda q: pytest.fail('Unexpected solve'))
    report = benchmark.run(1000, prepare_only=True)
    assert report['next_input'].endswith('words-28.json')
    empty = report['experiments'][0]
    assert empty['word_count'] == 0
    verify(HiddenRecoveryRequest.from_dict(empty['request']), empty['result'])
    assert empty['request']['ciphertext']['words'] == ()
    source = json.loads(benchmark.SOURCE.read_text())
    row = next(r for r in source['experiments'] if r['word_count'] == 29 and r['result']['status'] == 'UNSAT')
    base = HiddenRecoveryRequest.from_dict(row['request'])
    for n in range(1, 29):
        payload = json.loads((benchmark.ARTIFACTS/'budget-1000ms'/f'words-{n}.json').read_text())
        q = HiddenRecoveryRequest.from_dict(payload['request'])
        assert q.ciphertext.words == base.ciphertext.words[-n:]
        assert replace(q, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) == base


def test_unknown_preserves_bounds_and_larger_budget_retries_28(isolated, monkeypatch):
    calls = []
    def solve(request):
        calls.append((len(request.ciphertext.words), request.timeout_ms))
        return Recovery('UNKNOWN', 0)
    monkeypatch.setattr(benchmark, 'recover_observed_codes', solve)
    report = benchmark.run(1000)
    assert calls == [(28, 1000)]
    assert report['boundary']['smallest_proved_unsat'] == 29
    assert report['boundary']['largest_verified_sat'] == 0
    benchmark.run(2000, resume=True)
    assert calls == [(28, 1000), (28, 2000)]
    cached = json.loads(benchmark.OUTPUT.read_text())
    cached['experiments'][-1]['input_sha256'] = 'tampered'
    benchmark.OUTPUT.write_text(json.dumps(cached))
    with pytest.raises(ValueError, match='mismatch'):
        benchmark.run(2000, resume=True)


def test_first_deletion_unsat_enters_binary_search(isolated, monkeypatch):
    calls = []
    def solve(request):
        calls.append(len(request.ciphertext.words))
        return Recovery('UNSAT' if len(calls) == 1 else 'UNKNOWN', 0)
    monkeypatch.setattr(benchmark, 'recover_observed_codes', solve)
    report = benchmark.run(1000)
    assert calls == [28, 14]
    assert report['boundary']['smallest_proved_unsat'] == 28
    assert not report['complete']
