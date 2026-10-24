from dataclasses import asdict
import json

import pytest

pytest.importorskip('torch')
pytest.importorskip('transformers')

from benchmarks import word_mapping_neural_probe as probe
from benchmarks.word_mapping_neural_model import file_hashes
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.fixtures import generate


class FakeScorer:
    def __init__(self):
        self.inference_rows = 0

    def score(self, segments, *, context_radius):
        values = {'a': -1, 'b': -2, 'c': -3, 'd': -5}
        words = [w for s in segments for w in s]
        score = sum(values[w] for w in words) * (2 if context_radius is None else 1)
        self.inference_rows += len(words)
        return {'word_masked_log_sum': score, 'word_normalized_log_sum': score,
                'words': len(words), 'subwords': len(words)}


def test_frozen_selection_deduplicates_resumes_validates_and_rejects_tampering(tmp_path, monkeypatch):
    parent, model, output = tmp_path / 'parent', tmp_path / 'model', tmp_path / 'output'
    protocol = {'scope': 'test fixture'}
    write_json(parent / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    write_json(parent / 'validation.json', {'validated': True, 'manifest_sha256': digest(protocol)})
    for name in ('bundle-1', 'bundle-2', 'bundle-3', 'pooled'):
        public, truth = generate([('a', 'b', 'c', 'a', 'b')], source={}, seed=713)
        write_json(parent / name / 'study/fixtures/one-to-one.json', asdict(public))
        write_json(parent / name / 'study/truth/one-to-one.json', asdict(truth))
        owner = {w: cipher for cipher, w in truth.decoding.items()}
        replacement = {'objective_delta': 2, 'changes': [
            {'ciphertext': owner['a'], 'before': 'a', 'after': 'd'}]}
        swap = {'objective_delta': 1, 'changes': [
            {'ciphertext': owner['a'], 'before': 'a', 'after': 'b'},
            {'ciphertext': owner['b'], 'before': 'b', 'after': 'a'}]}
        audit = {'public_sha256': public.identity,
                 'examples': {'injective_replacement': [replacement], 'swap': [swap]}}
        for profile in ('mixture', 'trigram'):
            write_json(parent / name / f'neighborhood-{profile}.json', {'report': audit, 'sha256': digest(audit)})
    model.mkdir()
    (model / 'fake.weights').write_text('test weights')
    protocol = {'files_sha256': file_hashes(model)}
    write_json(model / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    monkeypatch.setattr(probe.WholeWordScorer, 'load', lambda *args, **kwargs: FakeScorer())
    probes, _ = probe.freeze_probes(parent)
    assert len(probes) == 8
    assert all(len(p['selected_by']) == 2 for p in probes)
    result = probe.run(parent, model, output)
    assert all(s['truth_preferred'] == 4 and s['tied'] == 4 for s in result['summaries'])
    assert probe.run(parent, model, output, resume=True) == result
    assert probe.run(parent, model, output, validate=True) == result
    assert json.loads((output / 'validation.json').read_text())['validated']
    with pytest.raises(ValueError, match='protocol/code changed'):
        probe.run(parent, model, output, top=1, resume=True)
    path = next((output / 'rows').glob('*.json'))
    saved = json.loads(path.read_text())
    saved['row']['id'] = 'tampered'
    write_json(path, {'row': saved['row'], 'sha256': digest(saved['row'])})
    with pytest.raises(ValueError, match='identity changed'):
        probe.run(parent, model, output, validate=True)
