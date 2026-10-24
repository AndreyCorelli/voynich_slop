from itertools import product
from voynich_smt.solver.candidate_semijoin import semijoin


def test_joint_support_prunes_when_unary_support_cannot():
    words, rounds, contradiction = semijoin(['xy', 'xy'], [['aa', 'bb', 'ab'], ['aa', 'bb']])
    assert words == [['aa', 'bb'], ['aa', 'bb']]
    assert not contradiction and rounds >= 2


def test_semijoin_preserves_all_global_assignments():
    ciphers = ['xyz', 'xy', 'yz']
    candidates = [['aaa', 'aab', 'abb', 'bbb'], ['aa', 'bb'], ['aa', 'ab', 'bb']]
    solutions = []
    for values in product('ab', repeat=3):
        key = dict(zip('xyz', values))
        decoded = [''.join(key[c] for c in cipher) for cipher in ciphers]
        if all(word in pool for word, pool in zip(decoded, candidates)): solutions.append(decoded)
    remaining, _, contradiction = semijoin(ciphers, candidates)
    assert not contradiction
    assert all(all(word in pool for word, pool in zip(solution, remaining)) for solution in solutions)
    assert remaining[0] == ['aaa', 'aab', 'bbb']


def test_combined_propagation_preserves_global_solution_set():
    from collections import Counter
    from voynich_smt.solver.candidate_semijoin import propagate_candidates
    ciphers = ['xyz', 'xy', 'yz']
    pools = [['aab', 'abb', 'aba', 'baa'], ['aa', 'ab', 'ba'], ['ab', 'ba', 'bb']]
    def solutions(candidates):
        found = set()
        for values in product('ab', repeat=3):
            if max(Counter(values).values()) > 2: continue
            key = dict(zip('xyz', values))
            if all(''.join(key[c] for c in cipher) in pool for cipher, pool in zip(ciphers, candidates)):
                found.add(values)
        return found
    remaining, domains, _, contradiction = propagate_candidates(ciphers, pools, 'ab', 2)
    assert not contradiction
    assert solutions(pools) == solutions(remaining)
    assert all(all(letter in domains[code] for code, letter in zip('xyz', values)) for values in solutions(pools))
