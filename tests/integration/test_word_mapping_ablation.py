from dataclasses import replace
import json
from pathlib import Path

import pytest

from benchmarks import word_mapping_ablation as ablation
from benchmarks import word_mapping_foundation as foundation
from voynich_smt.data.voynich import normalize as eva
from voynich_smt.word_mapping.corpora import from_segments


def test_development_ablation_pairing_resume_validation_and_no_truth_in_search(tmp_path, monkeypatch):
    if not Path('data/vendor/whitakers-words').exists():
        pytest.skip('Pinned morphology resource not cached')
    stream = from_segments([('in', 'terra', 'est'), ('aqua', 'est'),
        ('in', 'terram', 'uenit'), ('terra', 'bona', 'est'),
        ('aqua', 'bona', 'est'), ('reserved', 'testword')], 'caesar', source={})
    monkeypatch.setattr(foundation, 'caesar_stream', lambda: stream)
    manuscript = eva({}, '#=IVTFF Eva- 2.0\n<f1r>\n<f1r.1,@P0> ar.or')
    monkeypatch.setattr(foundation.Corpus, 'load', lambda path: manuscript)
    data, out = tmp_path / 'foundation', tmp_path / 'ablation'
    prepared = foundation.run(data, max_words=100, prepare_only=True)
    assert 'test_score' not in prepared and not (data / 'truth').exists()
    assert foundation.validate(data)['validated']
    plan = ablation.AblationPlan(seeds=(11, 22), budgets=(5, 10), fixture_kinds=('one-to-one',),
                                collapse_weights=(1,), controls=('position-shuffle',), archive_size=5)
    original_optimize = ablation.optimize
    seen = []
    def checked_optimize(model, candidates, public, config, directory, **kwargs):
        assert not hasattr(public, 'plaintext') and not hasattr(public, 'decoding')
        assert 'reserved' not in candidates.forms and 'testword' not in candidates.forms
        seen.append((config.seed, config.steps_per_restart, public.source))
        return original_optimize(model, candidates, public, config, directory, **kwargs)
    monkeypatch.setattr(ablation, 'optimize', checked_optimize)
    report = ablation.run(data, out, plan)
    assert len(seen) == len(plan.jobs()) == 56
    assert report['total_evaluations'] == 420
    assert len(report['paired_budget_comparisons']) == 14
    assert all(len(row['paired_seeds']) == 2 for row in report['paired_budget_comparisons'])
    assert ablation.validate(out)['validated']
    before = json.loads((out / 'report.json').read_text())
    assert ablation.run(data, out, plan, resume=True) == before
    assert len(seen) == 56  # completed jobs are not searched again
    with pytest.raises(ValueError, match='output exists'):
        ablation.run(data, out, plan)
    with pytest.raises(ValueError, match='changed'):
        ablation.run(data, out, replace(plan, budgets=(5, 20)), resume=True)
    row_path = next((out / 'runs').rglob('result.json'))
    row = json.loads(row_path.read_text())
    row['row']['best_objective'] += 1
    row_path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match='checksum'):
        ablation.validate(out)


@pytest.mark.parametrize('kwargs', [{'seeds': (1, 1)}, {'budgets': (10,)},
    {'budgets': (20, 10)}, {'collapse_weights': (0,)}, {'controls': ('invalid',)},
    {'fixture_kinds': ('invalid',)}, {'archive_size': 0}])
def test_invalid_ablation_plans(kwargs):
    with pytest.raises(ValueError):
        ablation.AblationPlan(**kwargs)
