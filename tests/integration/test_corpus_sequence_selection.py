import math

import pytest

from benchmarks import corpus_sequence_selection as benchmark
from benchmarks.l3_conflict import verify
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def test_smoothed_pairs_and_unseen_transitions():
    model=benchmark.train_model(['a','b','a','b'],['a','b','c'])
    assert benchmark.sequence_score(['a','b'],model)>benchmark.sequence_score(['a','c'],model)
    assert math.isfinite(benchmark.sequence_score(['c','c'],model))
    with pytest.raises(ValueError): benchmark.sequence_score(['z'],model)


def test_protocol_disjointness_and_positive_controls(tmp_path,monkeypatch):
    monkeypatch.setattr(benchmark,'OUT',tmp_path)
    prepared=benchmark.prepare()
    assert len(prepared['cases'])==4
    assert prepared['max_keys']==3 and prepared['timeout_ms']==5000
    for case in prepared['cases']:
        assert min(case['evaluation_record_indices'])>=prepared['split_record']
        if 'truth' in case:
            verify(HiddenRecoveryRequest.from_dict(case['request']),case['truth'])
    assert benchmark.digest(benchmark.prepare())==benchmark.digest(prepared)


def test_score_ignores_holdout_information():
    model=benchmark.train_model(['ab','ac','ab'],['ab','ac'])
    assert benchmark.sequence_score([['a','b'],['a','c']],model)==benchmark.sequence_score(['ab','ac'],model)
