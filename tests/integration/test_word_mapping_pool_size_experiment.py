from dataclasses import asdict
import json
import pytest
from benchmarks import word_mapping_pool_size as experiment
from benchmarks.word_mapping_neural_model import file_hashes
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.ngram import NgramModel


class FakeScorer:
    def __init__(self):
        self.cache = {}
        self.inference_rows = 0

    def score(self, segments):
        words = [w for s in segments for w in s]
        value = -sum({'a': 1, 'b': 2, 'c': 3, 'd': 4}[w] for w in words)
        self.inference_rows += len(words)
        return {'word_normalized_log_sum': value, 'word_masked_log_sum': value,
            'words': len(words), 'subwords': len(words)}


def test_matched_pools_truth_free_search_resume_validation_and_tampering(tmp_path, monkeypatch):
    parent, model_path, out = (tmp_path / n for n in ('parent', 'model', 'output'))
    training = [('a', 'a', 'a', 'b', 'b', 'c', 'd')]
    model = NgramModel.train(training, training_sha256='train')
    morphology = MorphologyCatalog({w: [] for w in 'abcd'}, {}, 'train')
    full = CandidateCatalog.build(training, morphology, training_sha256='train')
    monkeypatch.setattr(experiment, 'resources', lambda path: (model, morphology, full))
    monkeypatch.setattr(experiment, 'SIZES', (3, None))
    monkeypatch.setattr(experiment, 'BUNDLES', ('bundle-1',))
    monkeypatch.setattr(experiment, 'MODES', ('frequency', 'random'))
    monkeypatch.setattr(experiment, 'SEEDS', (101, 202))
    protocol = {'model_sha256': model.identity, 'candidate_sha256': digest(asdict(full))}
    write_json(parent / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    write_json(parent / 'validation.json', {'validated': True, 'manifest_sha256': digest(protocol)})
    public, truth = generate([('a', 'b', 'd')], source={}, seed=17)
    study = parent / 'bundle-1/study'
    write_json(study / 'fixtures/one-to-one.json', asdict(public))
    write_json(study / 'truth/one-to-one.json', asdict(truth))
    write_json(study / 'manifest.json', {'protocol': {'fixture_sha256': {'one-to-one': public.identity}}})
    model_path.mkdir()
    (model_path / 'weights').write_text('fake')
    protocol = {'files_sha256': file_hashes(model_path)}
    write_json(model_path / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    monkeypatch.setattr(experiment.WholeWordScorer, 'load', lambda *a, **k: FakeScorer())
    original = experiment.optimize
    seen = []
    def checked(model, candidates, public, config, directory, **kwargs):
        assert not hasattr(public, 'decoding')
        assert set(candidates.forms) <= set('abcd')
        seen.append((len(candidates.forms), config.steps_per_restart))
        return original(model, candidates, public, config, directory, **kwargs)
    monkeypatch.setattr(experiment, 'optimize', checked)
    report = experiment.run(parent, model_path, out, steps=10, shortlist=6)
    assert seen == [(3, 10)] * 4 + [(4, 10)] * 4
    assert report['rows'][0]['candidate_token_coverage'] == 2 / 3
    assert report['rows'][1]['candidate_token_coverage'] == 1
    for row in report['rows']:
        assert row['ngram']['exact_token_accuracy'] <= row['candidate_token_coverage']
        assert row['neural']['exact_token_accuracy'] <= row['candidate_token_coverage']
        assert row['neural_accuracy_on_supported_tokens'] == row['neural']['exact_token_accuracy'] / row['candidate_token_coverage']
    assert json.loads((out / 'search-report.json').read_text())['mutations'] == 80
    assert experiment.run(parent, model_path, out, steps=10, shortlist=6, resume=True) == report
    assert experiment.run(parent, model_path, out, steps=10, shortlist=6, validate=True) == report
    with pytest.raises(ValueError, match='protocol changed'):
        experiment.run(parent, model_path, out, steps=11, shortlist=6, resume=True)
    path = next((out / 'scores').glob('*.json'))
    saved = json.loads(path.read_text())
    saved['row']['score']['word_normalized_log_sum'] += 10
    saved['sha256'] = digest(saved['row'])
    write_json(path, saved)
    with pytest.raises(ValueError, match='recomputation'):
        experiment.run(parent, model_path, out, steps=10, shortlist=6, validate=True)
