from dataclasses import asdict
import json
import pytest
from benchmarks import word_mapping_diverse_rerank as rerank
from benchmarks.word_mapping_diverse_audit import audit
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


def test_diverse_pool_keeps_origins_recovers_and_rejects_tamper(tmp_path, monkeypatch):
    parent, generation, model, out = (tmp_path / n for n in ('parent', 'generation', 'model', 'out'))
    monkeypatch.setattr(rerank, 'ROOT', generation)
    protocol = {'test': True}
    parent_hash = digest(protocol)
    write_json(parent / 'manifest.json', {'protocol': protocol, 'sha256': parent_hash})
    hashes = {}
    for bundle in ('bundle-1', 'bundle-2', 'bundle-3', 'pooled'):
        public, truth = generate([('a', 'a', 'b', 'c')], source={}, seed=17)
        study = parent / bundle / 'study'
        write_json(study / 'fixtures/one-to-one.json', asdict(public))
        write_json(study / 'truth/one-to-one.json', asdict(truth))
        hashes[f'{bundle}/public'] = public.identity
        correct = {cipher: ['a', 'b', 'c'].index(word) for cipher, word in truth.decoding.items()}
        wrong = {cipher: {0: 1, 1: 0, 2: 2}[index] for cipher, index in correct.items()}
        archive = {'forms': ['a', 'b', 'c'], 'rows': [{'score': 2, 'assignments': wrong}, {'score': 1, 'assignments': correct}]}
        for seed in (11, 22, 33):
            write_json(study / f'runs/one-to-one/injective/seed-{seed}/budget-50000/original/archive.json', archive)
        for mode in rerank.MODES:
            for seed in rerank.SEEDS:
                write_json(generation / bundle / f'{mode}-{seed}/archive.json', archive)
                hashes[f'{bundle}/{mode}-{seed}'] = digest(archive)
    protocol = {'parent_sha256': parent_hash}
    write_json(generation / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    write_json(generation / 'report.json', {'source_sha256': hashes})
    write_json(generation / 'validation.json', {'validated': True, 'manifest_sha256': digest(protocol), 'source_sha256': hashes})
    model.mkdir()
    (model / 'weights').write_text('fake')
    protocol = {'files_sha256': file_hashes(model)}
    write_json(model / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    monkeypatch.setattr(rerank.WholeWordScorer, 'load', lambda *a, **k: FakeScorer())
    jobs, _ = rerank.freeze(parent, 3)
    assert all(len(j['candidates']) == 2 and j['pool_dictionaries'] == 18 for j in jobs)
    report = rerank.run(parent, model, out, top=3)
    assert report['summary']['improved'] == 4
    assert rerank.run(parent, model, out, top=3, resume=True) == report
    assert rerank.run(parent, model, out, top=3, validate=True) == report
    diagnostic = audit(out, parent, generation)
    assert all(r['pool_oracle_accuracy'] == 1 for r in diagnostic['rows'])
    assert all(r['shortlist_mean_pairwise_type_distance'] == 2 / 3 for r in diagnostic['rows'])
    path = generation / 'bundle-1/frequency-101/archive.json'
    data = json.loads(path.read_text())
    data['rows'][0]['score'] += 1
    write_json(path, data)
    with pytest.raises(ValueError, match='Generated archive changed'):
        rerank.freeze(parent, 3)
