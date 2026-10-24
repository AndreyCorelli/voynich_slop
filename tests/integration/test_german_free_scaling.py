from dataclasses import replace
import json
from pathlib import Path

import pytest

import benchmarks.german_free_scaling as benchmark
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def test_extensions_preserve_verified_model_and_exact_nested_prefix(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'ARTIFACTS', tmp_path/'inputs')
    monkeypatch.setattr(benchmark, 'OUTPUT', tmp_path/'report.json')
    report = benchmark.prepare(1000)
    sat = json.loads(benchmark.SAT.read_text())
    base = HiddenRecoveryRequest.from_dict(sat['request'])
    assert len(report['prepared_inputs']) == 9 and report['solver_calls'] == 0
    targets = []
    for entry in report['prepared_inputs']:
        payload = json.loads(Path(entry['public_input']).read_text())
        assert digest(payload) == entry['input_sha256']
        assert set(payload) == {'request', 'codeword_domains'}
        request = HiddenRecoveryRequest.from_dict(payload['request'])
        assert replace(request, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) == base
        if entry['kind'] == 'voynich':
            assert request.ciphertext.words[:23] == base.ciphertext.words
            targets.append(request.ciphertext.words)
        else:
            assert entry['generating_witness_verified']
    assert list(map(len, targets)) == [30, 40, 51]
    assert all(t == targets[-1][:len(t)] for t in targets)


@pytest.mark.parametrize('budget', [0, -1, True])
def test_invalid_budgets_rejected(budget):
    with pytest.raises(ValueError, match='positive integer'):
        benchmark.prepare(budget)
