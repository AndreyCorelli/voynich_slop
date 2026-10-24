from dataclasses import asdict
import json
import pytest
from benchmarks import word_mapping_phrase as phrase_experiment
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.ngram import NgramModel


@pytest.mark.parametrize('experiment', [phrase_experiment])
def test_ablations_truth_only_after_search_resume_validation_and_tamper(tmp_path, monkeypatch, experiment):
    parent, out = tmp_path / 'parent', tmp_path / 'out'
    training = [('terra', 'bona', 'est'), ('aqua', 'mala', 'est')] * 3
    model = NgramModel.train(training, training_sha256='train')
    entries = {}
    for w in ('terra', 'bona', 'aqua', 'mala', 'est'):
        pos = 'ADJ' if w in ('bona', 'mala') else ('V' if w == 'est' else 'N')
        entries[w] = [{'lemma_id': w, 'inflections': [{'part_of_speech': pos,
            'features': {'Case': 'NOM', 'Number': 'S', 'Gender': 'F'}}]}]
    morphology = MorphologyCatalog(entries, {}, 'train')
    catalog = CandidateCatalog.build(training, morphology, training_sha256='train')
    monkeypatch.setattr(experiment, 'resources', lambda path: (model, morphology, catalog))
    monkeypatch.setattr(experiment, 'BUNDLES', ('bundle-1',))
    monkeypatch.setattr(experiment, 'SEEDS', (11,))
    protocol = {'model_sha256': model.identity, 'candidate_sha256': digest(asdict(catalog)), 'morphology_sha256': morphology.identity}
    write_json(parent / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    write_json(parent / 'validation.json', {'validated': True, 'manifest_sha256': digest(protocol)})
    public, truth = generate([('terra', 'bona', 'est')], source={}, seed=17)
    study = parent / 'bundle-1/study'
    write_json(study / 'fixtures/one-to-one.json', asdict(public))
    write_json(study / 'truth/one-to-one.json', asdict(truth))
    write_json(study / 'manifest.json', {'protocol': {'fixture_sha256': {'one-to-one': public.identity}}})
    original = experiment.load_truth
    def checked_truth(*args):
        saved = json.loads((out / 'search-report.json').read_text())
        assert saved['searches'] == len(experiment.ARMS) and saved['mutations'] == len(experiment.ARMS) * 90
        assert all(json.loads(p.read_text())['restart'] == 3 for p in (out / 'runs').glob('*/*/*/checkpoint.json'))
        return original(*args)
    monkeypatch.setattr(experiment, 'load_truth', checked_truth)
    report = experiment.run(parent, out, steps=30)
    assert len(report['rows']) == len(report['summary']) == len(experiment.ARMS)
    assert report['mutations'] == len(experiment.ARMS) * 90
    assert all(sum(s['proposed'] for s in row['statistics'].values()) == 90 for row in report['rows'])
    assert experiment.run(parent, out, steps=30, resume=True) == report
    assert experiment.run(parent, out, steps=30, validate=True) == report
    with pytest.raises(ValueError, match='protocol changed'):
        experiment.run(parent, out, steps=31, resume=True)
    path = out / 'runs/bundle-1/phrase/seed-11/hypotheses.json'
    saved = json.loads(path.read_text())
    next(iter(saved.values()))['locked'] = True
    write_json(path, saved)
    with pytest.raises(ValueError, match='hypothesis support differs'):
        experiment.run(parent, out, steps=30, validate=True)
    # A missing export is rebuilt from the completed checkpoint during resume.
    path.unlink()
    assert experiment.run(parent, out, steps=30, resume=True) == report
