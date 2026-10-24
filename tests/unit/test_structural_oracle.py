import pytest
from voynich_smt.structural_oracle import StructuralOracle


def entry(pos, **features):
    return [{'enclitic': None, 'inflections': [{'part_of_speech': pos, 'features': features}]}]


def test_tolerance_ambiguity_and_unknown_are_distinct():
    entries = {'ager': entry('N', Case='NOM', Number='S', Gender='M'),
               'servus': entry('N', Case='NOM', Number='S', Gender='M'),
               'agrum': entry('N', Case='ACC', Number='S', Gender='M'),
               'ambiguous': entry('N', Case='NOM', Number='S', Gender='M') + entry('N', Case='ACC', Number='S', Gender='M'),
               'in': entry('PREP'), 'ad': entry('PREP')}
    oracle = StructuralOracle(entries, {'x': 'ager', 'y': 'in', 'z': 'unannotated'})
    assert oracle.status('x', 'servus') == 'compatible'
    assert oracle.status('x', 'agrum') == 'error'
    assert oracle.status('x', 'ambiguous') == 'error'
    assert oracle.status('x', 'ambiguous', permissive=True) == 'compatible'
    assert oracle.status('y', 'ad', permissive=True) == 'error'
    assert oracle.status('z', 'unannotated') == 'compatible'
    assert oracle.status('z', 'servus') == 'unknown'
    result = oracle.evaluate((('x', 'x', 'y', 'z'),), {'x': 'servus', 'y': 'ad', 'z': 'servus'})
    assert result['compatible'] == 2
    assert result['error_lower_bound'] == .25
    assert result['error_upper_bound'] == .5
    with pytest.raises(ValueError):
        oracle.evaluate((('x',),), {'x': 'servus'})


def test_enclitics_are_preserved():
    a = entry('N', Case='NOM')
    b = entry('N', Case='NOM')
    b[0]['enclitic'] = 'que'
    oracle = StructuralOracle({'a': a, 'b': b}, {'x': 'a'})
    assert oracle.status('x', 'b') == 'error'
