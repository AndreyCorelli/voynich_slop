from pathlib import Path

import pytest

from benchmarks import word_mapping_foundation as foundation
from benchmarks import word_mapping_recovery as benchmark
from voynich_smt.data.voynich import normalize as eva
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.corpora import from_segments


def test_complete_artifact_pipeline_and_control_budgets(tmp_path, monkeypatch):
    if not Path('data/vendor/whitakers-words').exists():
        pytest.skip('Pinned morphology resource not cached')
    words = [('in', 'terra', 'est'), ('aqua', 'est'), ('in', 'terram', 'uenit'),
             ('terra', 'bona', 'est'), ('aqua', 'bona', 'est'), ('in', 'terra', 'aqua')]
    stream = from_segments(words, 'caesar', source={'scope': 'integration fixture'})
    monkeypatch.setattr(foundation, 'caesar_stream', lambda: stream)
    manuscript = eva({}, '#=IVTFF Eva- 2.0\n<f1r>\n<f1r.1,@P0> ar.or')
    monkeypatch.setattr(foundation.Corpus, 'load', lambda path: manuscript)
    data = tmp_path / 'foundation'
    foundation.run(data, max_words=100)
    assert foundation.validate(data)['validated']
    config = SearchConfig(seed=22, restarts=2, steps_per_restart=25, active_types=10)
    out = tmp_path / 'search'
    result = benchmark.run(data, out, kind='one-to-one', config=config, controls=True)
    assert result['evaluations'] == 50
    assert len(result['controls']) == 3
    assert all(row['search']['evaluations'] == 50 for row in result['controls'])
    assert benchmark.validate(data, out, config)['validated']
    with pytest.raises(ValueError, match='Checkpoint exists'):
        benchmark.run(data, out, kind='one-to-one', config=config)
    assert benchmark.run(data, out, kind='one-to-one', config=config,
                         controls=True, resume=True)['recovery'] == result['recovery']
