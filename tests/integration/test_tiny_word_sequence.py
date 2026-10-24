import json

import pytest

from benchmarks import tiny_word_sequence as benchmark
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def request():
    return HiddenRecoveryRequest.from_dict(json.loads(benchmark.SOURCE.read_text())['request'])


def test_pair_constraint_rejects_impossible_adjacencies():
    q = request()
    # Nonempty vocabulary alone permits the observations; no allowed transitions cannot.
    assert benchmark.fit(q, ())['status'] == 'UNSAT'
    result = benchmark.fit(q, benchmark.allowed_pairs())
    assert result['status'] == 'SAT' and result['verified']
    assert benchmark.accepts(result['plaintext']['words'], benchmark.allowed_pairs())


def test_pair_validation():
    with pytest.raises(ValueError, match='two dictionary words'):
        benchmark.fit(request(), ((tuple('ab'), tuple('zz')),))


def test_fixed_protocol_and_training_selection(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path)
    report = benchmark.run()
    assert report['generating_training_pair_compatible']
    assert report['complete'] and len(report['solutions']) <= 6
    for row in report['solutions']:
        assert benchmark.accepts(row['result']['plaintext']['words'], benchmark.allowed_pairs())
    assert json.loads((tmp_path / 'protocol.json').read_text())['max_solutions'] == 6
    with pytest.raises(ValueError, match='do not overwrite'):
        benchmark.run()
