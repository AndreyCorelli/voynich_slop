import json
import pytest
from benchmarks import word_mapping_widening as widening
from benchmarks import word_mapping_zero_corruption as experiment
from voynich_smt.data.corpus import write_json
from voynich_smt.word_mapping.corpora import from_segments
from voynich_smt.word_mapping.morphology import MorphologyCatalog


def test_zero_start_parent_checks_full_replay_and_tamper(tmp_path, monkeypatch):
    train = from_segments([('a','b','c','d'), ('e','f','g','h')]*3, 'train', source={})
    dev = from_segments([('a','nova','b'), ('c','d'), ('e','a','b'), ('nova','b','c'),
                         ('a','d','g'), ('e','nova','f'), ('a','nova','g')], 'dev', source={})
    final = from_segments([('x','y','z')], 'final', source={})
    morphology = MorphologyCatalog({w: [] for s in train.segments() for w in s}, {}, train.identity)
    monkeypatch.setattr(widening, 'source_streams', lambda parent: (train,dev,final,morphology,'test-parent'))
    parent, out = tmp_path/'parent', tmp_path/'zero'
    options = dict(targets=(5,10), holdout_tokens=3, steps=40, seeds=(11,), restarts=3, workers=1)
    widening.run(out=parent, **options)
    widening.run(out=parent, validate=True, **options)
    report = experiment.run(parent, out, steps=60, seeds=(11,))
    assert report['runs'] == 4 and report['evaluations'] == 240
    for p in (out/'runs').glob('*/*/*/report.json'):
        row=json.loads(p.read_text())
        assert row['trace'][0]['current_recovery']['exact_token_accuracy'] == 1
        assert row['trace'][0]['current_recovery']['exact_type_accuracy'] == 1
        assert row['initial_holdout_recurring']['accuracy'] == 1
        assert sum(v['proposed'] for v in row['proposal_quality'].values()) == 60
    assert experiment.run(parent, out, steps=60, seeds=(11,), validate=True) == report
    with pytest.raises(ValueError, match='protocol differs'):
        experiment.run(parent, out, steps=61, seeds=(11,), validate=True)
    path = next((out/'runs').glob('*/*/*/report.json'))
    saved=json.loads(path.read_text())
    saved['proposal_quality']['up/down']['proposed'] += 1
    write_json(path,saved)
    with pytest.raises(ValueError, match='run differs'):
        experiment.run(parent, out, steps=60, seeds=(11,), validate=True)
