import ast
import json
from pathlib import Path

import pytest

from benchmarks.latin_contractions import applies, expand, scan, unitizations, validate_inventory


def inventory():
    return json.loads(Path('experiments/configs/latin-contractions.json').read_text())


def rule(identifier):
    return next(r for r in inventory()['rules'] if r['id'] == identifier)


@pytest.mark.parametrize('identifier,word,index,expected', [
    ('ae', 'caesar', 1, True), ('per', 'super', 2, True), ('pro', 'proprius', 0, True),
    ('con', 'contra', 0, True), ('con', 'recon', 2, False),
    ('et', 'et', 0, True), ('et', 'etiam', 0, False),
    ('est', 'est', 0, True), ('est', 'testis', 1, False),
    ('rum', 'eorum', 2, True), ('rum', 'ruma', 0, False),
])
def test_fixed_historical_rule_scopes(identifier, word, index, expected):
    assert applies(word, index, rule(identifier)) == expected


def test_optional_counts_and_distinct_units_round_trip():
    rules = inventory()['rules']
    for word in ['caesar', 'per', 'pro', 'contra', 'et', 'est', 'eorum', 'praeper']:
        paths = unitizations(word, rules)
        assert len(word) in paths
        assert all(len(path) == count and expand(path, rules) == word for count, path in paths.items())
    assert unitizations('ae', rules)[1] == ('<ae>',)
    assert unitizations('per', rules)[1] == ('<per>',)
    assert expand(('<per>',), rules) != expand(('<pro>',), rules)
    with pytest.raises(ValueError, match='Unknown unit'):
        expand(('<unknown>',), rules)


def test_overlapping_rules_do_not_double_count_and_keep_all_attainable_lengths():
    rules = [{'id': 'aba', 'expansion': 'aba', 'position': 'any'},
             {'id': 'ab', 'expansion': 'ab', 'position': 'any'}]
    paths = unitizations('ababa', rules)
    assert set(paths) == {2, 3, 4, 5}
    assert all(expand(path, rules) == 'ababa' for path in paths.values())


def test_contractions_are_optional_when_minimum_units_are_too_short():
    stats, candidates = scan([['est']], [rule('est')], [list('xxxx')])
    assert stats['positionwise_optional_length_compatible'] == 1
    assert candidates[0]['compatible_unit_counts_by_position'] == [[3]]
    assert candidates[0]['one_length_compatible_unitization'] == [['e', 's', 't']]


def test_gaps_and_source_boundaries_interrupt_windows():
    stats, candidates = scan([['et', None, 'est'], ['per']], inventory()['rules'], [list('x'), list('y')])
    assert stats['windows'] == 0 and not candidates


def test_reversible_contractions_do_not_remove_repetition_conflicts():
    stats, candidates = scan([['et', 'est']], inventory()['rules'], [list('x'), list('x')])
    assert stats['positionwise_optional_length_compatible'] == 1
    assert stats['positionwise_and_repetition_compatible'] == 0
    assert candidates[0]['equal_ciphertext_word_conflicts'][0]['left_plaintext'] == 'et'
    stats, candidates = scan([['et', 'et']], inventory()['rules'], [list('x'), list('x')])
    assert stats['positionwise_and_repetition_compatible'] == 1


def test_inventory_validation_rejects_unknown_profile_rules():
    config = inventory()
    validate_inventory(config)
    config['profiles']['invalid'] = ['invented']
    with pytest.raises(ValueError, match='profile'):
        validate_inventory(config)


def test_analysis_does_not_import_solver_or_z3():
    tree = ast.parse(Path('benchmarks/latin_contractions.py').read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(not n.name.startswith(('z3', 'voynich_smt')) for n in node.names)
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or '').startswith(('z3', 'voynich_smt'))
