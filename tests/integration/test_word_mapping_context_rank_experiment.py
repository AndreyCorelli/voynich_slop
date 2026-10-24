from dataclasses import asdict
import json
from types import SimpleNamespace
import pytest
from benchmarks import word_mapping_context_rank as experiment
from benchmarks.word_mapping_neural_model import file_hashes
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.ngram import NgramModel


class FakeScorer:
    tokenizer = SimpleNamespace(mask_token_id=99)
    batch_size = 16
    def __init__(self):
        self.inference_rows = 0
    def _job(self, words, target):
        ids = [0] + [ord(w) for w in words] + [2]
        labels = (ids[target + 1],)
        ids[target + 1] = 99
        return ids, (target + 1,), labels
    def _batch(self, jobs):
        self.inference_rows += len(jobs)
        return [(-sum(labels), len(labels)) for _, _, labels in jobs]


def test_oracle_contexts_nested_target_masking_frozen_resume_and_recompute(tmp_path, monkeypatch):
    parent, decoded, model_path, out = (tmp_path / n for n in ('parent', 'decoded', 'model', 'out'))
    training = [('a', 'a', 'b', 'c', 'd')]
    model = NgramModel.train(training, training_sha256='train')
    morphology = MorphologyCatalog({w: [] for w in 'abcd'}, {}, 'train')
    catalog = CandidateCatalog.build(training, morphology, training_sha256='train')
    monkeypatch.setattr(experiment, 'resources', lambda path: (model, morphology, catalog))
    protocol = {'model_sha256': model.identity, 'candidate_sha256': digest(asdict(catalog))}
    parent_hash = digest(protocol)
    write_json(parent / 'manifest.json', {'protocol': protocol, 'sha256': parent_hash})
    write_json(parent / 'validation.json', {'validated': True, 'manifest_sha256': parent_hash})
    jobs = []
    for bundle in ('bundle-1', 'bundle-2', 'bundle-3'):
        public, truth = generate([('a', 'b', 'c', 'a')], source={}, seed=17)
        study = parent / bundle / 'study'
        write_json(study / 'fixtures/one-to-one.json', asdict(public))
        write_json(study / 'truth/one-to-one.json', asdict(truth))
        assignments = {w: (catalog.forms.index(gold) + 1) % len(catalog.forms) for w, gold in truth.decoding.items()}
        jobs.append({'bundle': bundle, 'size': len(catalog.forms), 'candidates': [{'assignments': assignments}]})
    protocol = {'parent_sha256': parent_hash}
    decoded_hash = digest(protocol)
    write_json(decoded / 'manifest.json', {'protocol': protocol, 'sha256': decoded_hash})
    write_json(decoded / 'validation.json', {'validated': True, 'manifest_sha256': decoded_hash})
    write_json(decoded / 'selection.json', jobs)
    write_json(decoded / 'report.json', {'selection_sha256': digest(jobs), 'manifest_sha256': decoded_hash})
    probes, _, _, _ = experiment.freeze(parent, decoded, targets=3)
    assert len(probes) == 9
    for probe in probes:
        assert probe['candidates'][probe['gold_index']] == probe['gold']
        assert probe['contexts']['correct-0']['neighbor_token_accuracy'] == 0
        assert probe['contexts']['correct-100']['neighbor_token_accuracy'] == 1
        values = [probe['contexts'][f'correct-{n}']['neighbor_token_accuracy'] for n in (0, 25, 50, 75, 100)]
        assert values == sorted(values)
    model_path.mkdir()
    (model_path / 'weights').write_text('fake')
    protocol = {'files_sha256': file_hashes(model_path)}
    write_json(model_path / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    monkeypatch.setattr(experiment.WholeWordScorer, 'load', lambda *a, **k: FakeScorer())
    report = experiment.run(parent, decoded, model_path, out, targets=3)
    assert len(report['summary']) == 24
    assert experiment.run(parent, decoded, model_path, out, targets=3, resume=True) == report
    assert experiment.run(parent, decoded, model_path, out, targets=3, validate=True) == report
    with pytest.raises(ValueError, match='protocol changed'):
        experiment.run(parent, decoded, model_path, out, targets=2, resume=True)
    path = next((out / 'rows').glob('*.json'))
    saved = json.loads(path.read_text())
    saved['row']['contexts']['correct-100']['scores']['neural_raw'][0] += 10
    saved['sha256'] = digest(saved['row'])
    write_json(path, saved)
    with pytest.raises(ValueError, match='recomputation differs'):
        experiment.run(parent, decoded, model_path, out, targets=3, validate=True)
