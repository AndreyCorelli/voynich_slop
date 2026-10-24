import json
import pytest
from benchmarks import word_mapping_widening as experiment
from benchmarks import word_mapping_widening_initialization as initialization
from voynich_smt.data.corpus import write_json
from voynich_smt.word_mapping.corpora import from_segments
from voynich_smt.word_mapping.morphology import MorphologyCatalog


def test_widening_truth_isolation_serial_parallel_validation_and_resume(tmp_path, monkeypatch):
    train = from_segments([('a', 'b', 'c', 'd'), ('e', 'f', 'g', 'h')]*3, 'train', source={})
    dev = from_segments([('a', 'nova', 'b'), ('c', 'd'), ('e', 'a', 'b'), ('nova', 'b', 'c'),
                         ('a', 'd', 'g'), ('e', 'nova', 'f'), ('a', 'nova', 'g')], 'dev', source={})
    final = from_segments([('x', 'y', 'z')], 'final', source={})
    morphology = MorphologyCatalog({w: [] for s in train.segments() for w in s}, {}, train.identity)
    monkeypatch.setattr(experiment, 'source_streams', lambda parent: (train, dev, final, morphology, 'test-parent'))
    options = dict(targets=(5, 10), holdout_tokens=3, steps=40, seeds=(11,), restarts=3)
    out = tmp_path / 'serial'
    original = experiment.load_truth
    def isolated(path):
        directory = path.parent.parent
        phase = json.loads((directory / 'search-report.json').read_text())
        assert phase['searches'] == 6
        assert all(json.loads(p.read_text())['restart'] == 3 for p in (directory / 'runs').glob('*/*/*/*/checkpoint.json'))
        return original(path)
    monkeypatch.setattr(experiment, 'load_truth', isolated)
    report = experiment.run(out=out, workers=1, **options)
    assert report['unique_searches'] == 6
    assert all(r['candidate_token_coverage'] == 1 for r in report['rows'] if r['job']['coverage'] == 'oracle')
    assert any(r['candidate_token_coverage'] < 1 for r in report['rows'] if r['job']['coverage'] == 'training')
    assert experiment.run(out=out, workers=1, resume=True, **options) == report
    assert experiment.run(out=out, workers=1, validate=True, **options) == report
    diagnostic = initialization.run(out)
    assert initialization.run(out, validate=True) == diagnostic
    assert len(diagnostic['rows']) == 2
    parallel = experiment.run(out=tmp_path/'parallel', workers=2, **options)
    assert [r['archive_sha256'] for r in parallel['rows']] == [r['archive_sha256'] for r in report['rows']]
    assert parallel['summary'] == report['summary']
    with pytest.raises(ValueError, match='protocol changed'):
        experiment.run(out=out, workers=1, resume=True, **{**options, 'steps':41})
    path = out/'candidates-oracle.json'
    saved = json.loads(path.read_text())
    saved['form_counts']['nova'] = 1
    write_json(path, saved)
    with pytest.raises(ValueError, match='Foundation export differs'):
        experiment.run(out=out, validate=True, **options)
