from dataclasses import replace
import json
from pathlib import Path

import pytest

import benchmarks.german_free_extension as benchmark
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.settings import HomophoneSelection


def test_matched_inputs_change_only_selection_and_keep_truth_out(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'ARTIFACTS', tmp_path/'inputs')
    monkeypatch.setattr(benchmark, 'OUTPUT', tmp_path/'report.json')
    report = benchmark.prepare()
    assert report['solver_calls'] == 0 and len(report['prepared_inputs']) == 3
    for row in report['prepared_inputs']:
        old = json.loads(Path(row['cyclic_public_input']).read_text())
        new = json.loads(Path(row['public_input']).read_text())
        assert set(new) == {'request', 'codeword_domains'}
        assert digest(new) == row['input_sha256']
        original = HiddenRecoveryRequest.from_dict(old['request'])
        free = HiddenRecoveryRequest.from_dict(new['request'])
        assert free.selection == HomophoneSelection()
        assert replace(free, selection=original.selection) == original
        if row['kind'] == 'control':
            assert row['generating_witness_verified']


def test_comparison_rejects_noncyclic_source_and_wrong_wrapper():
    source = json.loads(benchmark.SOURCE.read_text())
    entry = next(r for r in source['prepared_inputs'] if r['id'] == 'voynich-23')
    original = json.loads(Path(entry['public_input']).read_text())
    with pytest.raises(ValueError, match='wrapper'):
        benchmark.free_variant({**original, 'truth': {}})
    original['request']['selection'] = {'mode': 'free', 'reset': 'text'}
    with pytest.raises(ValueError, match='cyclic'):
        benchmark.free_variant(original)
