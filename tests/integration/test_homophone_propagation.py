from itertools import product
from collections import Counter
from voynich_smt.solver.homophone_propagation import propagate_candidates


def solutions(cipher, candidates):
    codes = sorted({c for w in cipher for c in w}); out = set()
    for values in product('ab', repeat=len(codes)):
        if max(Counter(values).values()) > 2: continue
        key = dict(zip(codes, values))
        if all(''.join(key[c] for c in word) in pool for word,pool in zip(cipher,candidates)):
            out.add(values)
    return out


def test_propagation_preserves_every_global_solution():
    cipher = [['x','y'], ['y','z'], ['x','z']]
    inventory = ['aa','ab','ba','bb']
    pools = [inventory, ['aa','ab'], ['ab','bb']]
    pruned, domains, rounds, contradiction = propagate_candidates(cipher, pools, 'ab', 2)
    assert not contradiction and rounds >= 1
    assert solutions(cipher, pools) == solutions(cipher, pruned)
    assert domains['z'] == {'b'}


def test_capacity_and_empty_support_contradictions():
    cipher = [['x'], ['y'], ['z']]
    assert propagate_candidates(cipher, [['a'],['a'],['a']], 'ab', 2)[3]
    assert propagate_candidates([['x'],['x']], [['a'],['b']], 'ab', 2)[3]
    pruned, domains, _, contradiction = propagate_candidates(cipher, [['a'],['a'],['a','b']], 'ab', 2)
    assert not contradiction and domains['z'] == {'b'} and pruned[-1] == ['b']
