from dataclasses import asdict
import json
import pytest
from benchmarks import word_mapping_neural_rerank as rerank
from benchmarks.word_mapping_neural_model import file_hashes
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.fixtures import generate


class FakeScorer:
    def __init__(self):
        self.cache = {}
        self.inference_rows = 0

    def score(self, segments):
        words = [w for s in segments for w in s]
        score = -sum({'a': 1, 'b': 4, 'c': 9}[w] for w in words)
        self.inference_rows += len(words)
        return {'word_masked_log_sum': score, 'word_normalized_log_sum': score,
                'words': len(words), 'subwords': len(words)}


def test_rerank_recovery_resume_validation_and_tamper(tmp_path, monkeypatch):
    parent, model, out = (tmp_path / n for n in ('parent', 'model', 'out'))
    protocol = {'test': True}
    write_json(parent / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    write_json(parent / 'validation.json', {'validated': True, 'manifest_sha256': digest(protocol)})
    for bundle in ('bundle-1', 'bundle-2', 'bundle-3', 'pooled'):
        public, truth = generate([('a', 'a', 'b', 'c')], source={}, seed=17)
        study = parent / bundle / 'study'
        write_json(study / 'fixtures/one-to-one.json', asdict(public))
        write_json(study / 'truth/one-to-one.json', asdict(truth))
        correct = {cipher: ['a', 'b', 'c'].index(word) for cipher, word in truth.decoding.items()}
        wrong = {cipher: {0: 1, 1: 0, 2: 2}[index] for cipher, index in correct.items()}
        for profile in ('injective', 'trigram'):
            for seed in (11, 22):
                write_json(study / f'runs/one-to-one/{profile}/seed-{seed}/budget-50000/original/archive.json',
                    {'forms': ['a', 'b', 'c'], 'rows': [{'score': 2, 'assignments': wrong}, {'score': 1, 'assignments': correct}]})
    model.mkdir()
    (model / 'weights').write_text('fake')
    protocol = {'files_sha256': file_hashes(model)}
    write_json(model / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    monkeypatch.setattr(rerank.WholeWordScorer, 'load', lambda *a, **k: FakeScorer())
    report = rerank.run(parent, model, out, top=2)
    assert report['summary']['improved'] == 16
    assert report['summary']['mean_before'] == .25
    assert report['summary']['mean_after'] == 1
    assert rerank.run(parent, model, out, top=2, resume=True) == report
    assert rerank.run(parent, model, out, top=2, validate=True) == report
    with pytest.raises(ValueError, match='protocol changed'):
        rerank.run(parent, model, out, top=1, resume=True)
    path = next((out / 'scores').glob('*.json'))
    saved = json.loads(path.read_text())
    saved['row']['score']['word_normalized_log_sum'] += 10
    saved['sha256'] = digest(saved['row'])
    write_json(path, saved)
    with pytest.raises(ValueError, match='recomputation differs'):
        rerank.run(parent, model, out, top=2, validate=True)
