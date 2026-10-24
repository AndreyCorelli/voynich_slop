from dataclasses import replace
import copy
import json
from pathlib import Path

import pytest

import benchmarks.german_cyclic_scaling as scaling
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.solver.recovery import Recovery


@pytest.fixture(scope='module')
def prepared(tmp_path_factory):
    original = scaling.ARTIFACTS
    scaling.ARTIFACTS = tmp_path_factory.mktemp('cyclic-artifacts')
    try:
        return scaling.prepare(1000, 1000)
    finally:
        scaling.ARTIFACTS = original


def test_source_o_occurrences_are_in_attested_line(prepared):
    occurrences = prepared['source_audit']['occurrences']
    assert [o['word_number'] for o in occurrences] == ['1177', '1181']
    assert all(o['raw_form'] == 'o' for o in occurrences)
    assert occurrences[0]['line_words'] == ['o', 'du', 'edele', 'sele', 'o', 'du', 'edele', 'creatur']


def test_public_requests_keep_fixed_model_and_truth_separate(prepared):
    inputs = prepared['prepared_inputs']
    source = json.loads(scaling.BASELINE.read_text())
    base = HiddenRecoveryRequest.from_dict(next(r for r in source['experiments'] if r['source_id'] == 143)['request'])
    target = next(e for e in inputs if e['id'] == 'voynich-51')
    maximum = json.loads(Path(target['public_input']).read_text())['request']['ciphertext']['words']
    for entry in inputs:
        payload = json.loads(Path(entry['public_input']).read_text())
        assert set(payload) == {'request', 'codeword_domains'}
        assert digest(payload) == entry['input_sha256']
        request = HiddenRecoveryRequest.from_dict(payload['request'])
        assert request.selection == HomophoneSelection('cycle', 'text')
        assert replace(request, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) == base
        if entry['kind'] == 'voynich':
            assert payload['request']['ciphertext']['words'] == maximum[:entry['word_count']]
        else:
            truth = json.loads(Path(entry['truth_path']).read_text())
            assert digest(truth) == entry['truth_sha256']
            assert entry['generating_witness_verified']
    for seed in (7, 17):
        rows = [e for e in inputs if e['id'].endswith(f'seed-{seed}')]
        truth = [json.loads(Path(e['truth_path']).read_text()) for e in rows]
        assert all(t['encoder'] == truth[0]['encoder'] for t in truth)
        assert all(t['plaintext']['words'] == truth[-1]['plaintext']['words'][:e['word_count']]
                   for e, t in zip(rows, truth))


def test_checkpoint_unknown_does_not_become_unsat_and_resume_skips(prepared, tmp_path, monkeypatch):
    monkeypatch.setattr(scaling, 'prepare', lambda *args: copy.deepcopy(prepared))
    monkeypatch.setattr(scaling, 'RESULTS', tmp_path)
    calls = []
    def solve(request):
        calls.append(request)
        return Recovery('UNKNOWN', 0, reason_unknown='test budget')
    monkeypatch.setattr(scaling, 'recover_observed_codes', solve)
    report = scaling.run(1000, 1000, (23,), solve=True)
    assert len(calls) == 3 and not report['complete']
    assert report['smallest_proved_unsat'] is None and not report['minimality_proven']
    assert 23 in report['unresolved_sizes']
    scaling.run(1000, 1000, (23,), solve=True, resume=True)
    assert len(calls) == 3
    path = tmp_path/'budget-1000-controls-1000ms.json'
    cached = json.loads(path.read_text());cached['experiments'][0]['input_sha256'] = 'tampered'
    path.write_text(json.dumps(cached))
    with pytest.raises(ValueError, match='mismatch'):
        scaling.run(1000, 1000, (23,), solve=True, resume=True)


def test_positive_control_unsat_stops_before_voynich(prepared, tmp_path, monkeypatch):
    monkeypatch.setattr(scaling, 'prepare', lambda *args: copy.deepcopy(prepared))
    monkeypatch.setattr(scaling, 'RESULTS', tmp_path)
    calls = []
    def solve(request):
        calls.append(request)
        return Recovery('UNSAT', 0)
    monkeypatch.setattr(scaling, 'recover_observed_codes', solve)
    with pytest.raises(RuntimeError, match='positive control'):
        scaling.run(1000, 1000, (23,), solve=True)
    assert len(calls) == 1


def test_boundary_requires_adjacent_proven_sizes():
    report = {'experiments': [{'kind': 'voynich', 'word_count': 30, 'result': {'status': 'UNSAT'}}]}
    scaling.update_boundary(report)
    assert report['largest_verified_sat'] == 22 and not report['minimality_proven']
    report['experiments'].append({'kind': 'voynich', 'word_count': 23, 'result': {'status': 'UNSAT'}})
    scaling.update_boundary(report)
    assert report['minimality_proven'] and report['unresolved_sizes'] == []
