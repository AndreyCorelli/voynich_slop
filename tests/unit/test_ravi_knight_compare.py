import json

import pytest

from benchmarks.ravi_knight_english_compare import compare


def test_declared_factor_only_and_legacy_defaults(tmp_path):
    stage = {'types': 2, 'source': {}, 'cipher_vocabulary': ['<UNKNOWN>', 'x'],
             'candidate_token_ceiling': .5, 'token_accuracy': .2, 'log_likelihoods': [-5., -4.],
             'converged': False, 'frozen': [], 'inconsistent_cipher_types': 1}
    before = {'protocol': {'max_iterations': 200}, 'public_sha256': 'same',
              'runs': [{'seed': 3, 'stages': [stage]}], 'elapsed_seconds': 1.,
              'frequency': {'token_accuracy': .1}}
    after = json.loads(json.dumps(before))
    after['protocol'].update(initialization='frequency', freeze=True, frequency_strength=.5)
    left, right = tmp_path / 'before', tmp_path / 'after'
    left.mkdir(); right.mkdir()
    (left / 'result.json').write_text(json.dumps(before))
    (right / 'result.json').write_text(json.dumps(after))
    assert compare(left, right, vary='initialization')['before_setting'] == 'random'
    with pytest.raises(ValueError, match='Protocols differ'):
        compare(left, right)
    after['protocol']['freeze'] = False
    (right / 'result.json').write_text(json.dumps(after))
    with pytest.raises(ValueError, match='Protocols differ'):
        compare(left, right, vary='initialization')
