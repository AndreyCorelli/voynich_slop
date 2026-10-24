from dataclasses import replace
import json
from pathlib import Path

import pytest

from benchmarks import word_mapping_ablation as ablation
from benchmarks import word_mapping_foundation as foundation
from benchmarks import word_mapping_full_coverage as covered
from benchmarks import word_mapping_parallel as parallel
from voynich_smt.data.voynich import normalize as eva
from voynich_smt.word_mapping.corpora import WordStream, from_segments


def test_covered_expansion_and_parallel_search_matches_serial(tmp_path, monkeypatch):
    if not Path('data/vendor/whitakers-words').exists():
        pytest.skip('Pinned morphology resource not cached')
    stream = from_segments([('in', 'terra', 'est'), ('aqua', 'est', 'terra'),
        ('terra', 'noua', 'est'), ('reserved', 'testword', 'est'),
        ('in', 'aqua', 'est'), ('terra', 'bona', 'est'),
        ('noua', 'aqua', 'est'), ('bona', 'terra', 'est')], 'caesar', source={})
    monkeypatch.setattr(foundation, 'caesar_stream', lambda: stream)
    manuscript = eva({}, '#=IVTFF Eva- 2.0\n<f1r>\n<f1r.1,@P0> ar.or')
    monkeypatch.setattr(foundation.Corpus, 'load', lambda path: manuscript)
    parent = tmp_path / 'parent'
    foundation.run(parent, max_words=12, prepare_only=True)
    prepared = tmp_path / 'covered'
    manifest, audit = covered.prepare_foundation(parent, prepared, minimum_words=2)
    assert audit['admitted_tokens'] == 3
    assert covered.validate_foundation(prepared)['validated']
    training = WordStream.load(prepared / 'splits/train.json')
    words = {w for s in training.segments() for w in s}
    assert 'noua' in words and 'reserved' not in words and 'testword' not in words
    plan = ablation.AblationPlan(seeds=(1, 2), budgets=(5, 10), restarts=2,
        fixture_kinds=('one-to-one',),
        arm_names=('baseline', 'trigram', 'frequency-1', 'injective-frequency-1'),
        frequency_weights=(1.0,), constraint_arms=True,
        controls=('position-shuffle',), control_arm_names=('baseline',), all_types_active=True,
        archive_size=5)
    serial_out, parallel_out = tmp_path / 'serial', tmp_path / 'parallel'
    serial = ablation.run(prepared, serial_out, plan)
    result = parallel.run(prepared, parallel_out, plan, workers=2, checkpoint_every=3)
    assert result == serial
    assert ablation.validate(parallel_out)['validated']
    assert parallel.run(prepared, parallel_out, plan, workers=2, resume=True) == result
    for path in (parallel_out / 'runs').rglob('result.json'):
        row = json.loads(path.read_text())['row']
        assert row['score']['covered_tokens'] == row['score']['total_tokens']
        if row['recovery']:
            assert row['truth_diagnostic']['active_truth_feasible']
            assert row['truth_diagnostic']['comparison_scope'] == 'complete_active_dictionary'
            assert row['truth_diagnostic']['candidate_constrained_token_accuracy_ceiling'] == 1
    with pytest.raises(ValueError, match='changed'):
        parallel.run(prepared, parallel_out, replace(plan, budgets=(5, 20)), workers=2, resume=True)
