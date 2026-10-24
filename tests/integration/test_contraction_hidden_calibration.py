from benchmarks.contraction_hidden_calibration import (
    applies, core, expand, expansion_table, parts, variants, encoder_for,
)
from benchmarks.contraction_hidden_calibration_run import oracle_case
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.cipher.base import generate_ciphertext
import json
from pathlib import Path


def rules():
    return core(json.loads(Path('experiments/configs/latin-contractions-broader-v1.json').read_text()))


def test_all_core_costs_and_expansions_preserved():
    rs = rules(); table = expansion_table(rs)
    assert len(rs) == 27
    for r in rs:
        labels = tuple(s for s, _ in parts(r))
        assert len(labels) == r['units']
        assert expand(labels, table) == r['expansion']
    assert len(parts(next(r for r in rs if r['id'] == 'que'))) == 2
    assert len(parts(next(r for r in rs if r['id'] == 'sacred-dominus'))) == 3


def test_optional_variants_preserve_scope_context_and_spelling():
    rs = rules(); table = expansion_table(rs)
    for word in ['et', 'etiam', 'conperit', 'quarum', 'quicquid', 'dominus', 'abus', 'focus']:
        paths = variants(word, rs)
        assert tuple(word) in paths
        assert len(paths) == len(set(paths))
        assert all(expand(p, table) == word for p in paths)
    us = next(r for r in rs if r['id'] == 'us-after-b')
    assert applies('abus', 2, us)
    assert not applies('focus', 3, us)
    assert not any('<et-part-0>' in p for p in variants('etiam', rs))


def test_mixed_generator_is_reversible_and_exercises_both_widths():
    alphabet = Alphabet(tuple('abcdefghijklmnop'))
    encoder, _ = encoder_for(alphabet, 2, True, 123)
    assert {len(c) for cs in encoder.codebook.values() for c in cs} == {1, 2}
    plain = Text((alphabet.symbols, alphabet.symbols))
    ciphertext, _ = generate_ciphertext(plain, encoder, 124)
    assert encoder.decode(ciphertext) == plain


def test_oracle_adapter_does_not_mutate_frozen_lengths():
    original = {'oracle_segmentation': [[1, 2, 1], [2]], 'request': {'untouched': True}}
    corrected = oracle_case(original)
    assert corrected['oracle_segmentation'] == [[0, 1, 3, 4], [0, 2]]
    assert original['oracle_segmentation'] == [[1, 2, 1], [2]]
    assert corrected['request'] == original['request']


def test_independent_enumeration_matches_optional_overlap_paths():
    from benchmarks.contraction_hidden_validation import independent_paths
    rs = rules()
    for word in ['conperit', 'quarum', 'aeque', 'dominus', 'etiam']:
        assert independent_paths(word, rs) == set(variants(word, rs))


def test_prediction_novelty_is_stable_after_json_normalization():
    # Frozen raw runner produced list/tuple mismatch; validation uses JSON-normalized
    # cases and checks exact tuple membership independently before saving corrections.
    from benchmarks.contraction_hidden_calibration import prediction
    case = {'request': {'ciphertext': {'words': [['x']]}},
            'held_cipher': {'words': [['x'], ['y']]}, 'source': 'tiny',
            'held_plaintext': ['et', 'est'], 'generating_covered_mask': [True, False],
            'held_dictionary_mask': [True, True]}
    result = {'status': 'SAT', 'encoder': {'codebook': {'<et-part-0>': [['x']], '<est-part-0>': [['y']]}}}
    p = {'expansions': {'<et-part-0>': 'et', '<est-part-0>': 'est'},
         'fixtures': {'tiny': {'vocabulary': ['et', 'est']}}}
    output = prediction(json.loads(json.dumps(case)), result, p)
    assert output['exact'] == 2
    assert output['novel_exact'] == 1
    assert output['novel_words'] == 1
