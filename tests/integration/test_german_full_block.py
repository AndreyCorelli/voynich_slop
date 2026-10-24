from dataclasses import replace
import json
from pathlib import Path

import pytest

import benchmarks.german_full_block as benchmark
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def test_full_block_restores_verified_subset_and_preserves_all_cipher_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'ARTIFACTS', tmp_path/'inputs')
    monkeypatch.setattr(benchmark, 'OUTPUT', tmp_path/'report.json')
    report = benchmark.prepare()
    payload = json.loads(Path(report['public_input']).read_text())
    assert digest(payload) == report['input_sha256']
    assert set(payload) == {'request', 'codeword_domains'}
    full = HiddenRecoveryRequest.from_dict(json.loads(benchmark.FULL.read_text())['request'])
    request = HiddenRecoveryRequest.from_dict(payload['request'])
    assert len(request.ciphertext.words) == 30 and request.ciphertext == full.ciphertext
    assert replace(request, dictionary=full.dictionary, plaintext_alphabet=full.plaintext_alphabet,
                   timeout_ms=full.timeout_ms) == full
    source = json.loads(benchmark.ROBUSTNESS.read_text())
    entry = next(e for e in source['experiments'] if e['source_id'] == 133)
    subset = HiddenRecoveryRequest.from_dict(json.loads(Path(entry['public_input']).read_text())['request'])
    assert tuple(request.ciphertext.words[p-1] for p in report['subset_original_positions']) == subset.ciphertext.words
    assert replace(request, ciphertext=subset.ciphertext, timeout_ms=subset.timeout_ms) == subset


@pytest.mark.parametrize('source,budget', [(143, 1000), (133, 0), (133, True)])
def test_invalid_source_or_budget_rejected(source, budget):
    with pytest.raises(ValueError, match='surviving'):
        benchmark.prepare(source, budget)
