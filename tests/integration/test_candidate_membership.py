import pytest
import z3
from voynich_smt.solver.candidate_membership import candidate_membership


def test_direct_relation_equivalent_with_repeated_codes_and_invalid_candidates():
    letters = {'x': z3.Int('x'), 'y': z3.Int('y')}; cipher = ['x','y','x']
    candidates = ['aaa','aba','abb']
    equalities = {(code,letter): var == i for code,var in letters.items() for i,letter in enumerate('ab')}
    direct = candidate_membership(letters, cipher, candidates, equalities)
    flat = z3.Or([z3.And([letters[c] == 'ab'.index(letter) for c,letter in zip(cipher,w)]) for w in candidates])
    solver = z3.Solver(); solver.add(z3.Xor(direct, flat)); assert solver.check() == z3.unsat
    solver = z3.Solver(); solver.add(direct, letters['x'] == 0, letters['y'] == 1); assert solver.check() == z3.sat


def test_empty_relation_and_bad_lengths():
    assert z3.is_false(z3.simplify(candidate_membership({}, [], [], {})))
    with pytest.raises(ValueError): candidate_membership({}, ['x'], ['ab'], {})
