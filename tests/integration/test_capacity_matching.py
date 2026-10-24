from itertools import product
from collections import Counter
from voynich_smt.solver.capacity_matching import supported_domains


def test_capacity_support_matches_exhaustive_assignments():
    choices = ({'a'}, {'b'}, {'a', 'b'})
    for capacity in (1, 2):
        for selected in product(choices, repeat=3):
            domains = dict(enumerate(selected))
            solutions = [values for values in product(*selected) if max(Counter(values).values()) <= capacity]
            actual, contradiction = supported_domains(domains, capacity)
            assert contradiction == (not solutions)
            if solutions:
                assert actual == {i: {values[i] for values in solutions} for i in domains}


def test_hall_set_prunes_without_singletons():
    domains = {i: {'a', 'b'} for i in range(4)}
    domains[4] = {'a', 'b', 'c'}
    supported, contradiction = supported_domains(domains, 2)
    assert not contradiction and supported[4] == {'c'}
