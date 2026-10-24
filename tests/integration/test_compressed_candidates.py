import pytest
import z3
from voynich_smt.solver.compressed_candidates import compressed_membership
from voynich_smt.solver.candidate_membership import candidate_membership


@pytest.mark.parametrize('mode', ['dag','defined','layered'])
@pytest.mark.parametrize('cipher', ['xyz','xyx'])
def test_compression_equivalent_to_exact_candidate_relation(mode, cipher):
    eq = {(c,l): z3.Bool(f'{c}_{l}') for c in set(cipher) for l in 'ab'}
    pools = [[], ['aaa','aba','abb','bab','bbb']]
    for index, pool in enumerate(pools):
        solver=z3.Solver()
        solver.add([z3.PbEq([(eq[c,l],1) for l in 'ab'],1) for c in set(cipher)])
        direct=candidate_membership({}, cipher, pool, eq)
        compressed=compressed_membership(cipher,pool,eq,f'{mode}_{index}',mode)
        # Auxiliary-state encodings are existential: compare under every assignment.
        from itertools import product
        for values in product('ab',repeat=len(set(cipher))):
            solver.push()
            solver.add([eq[c,l] for c,l in zip(sorted(set(cipher)),values)])
            expected=''.join(dict(zip(sorted(set(cipher)),values))[c] for c in cipher) in pool
            solver.add(compressed)
            assert (solver.check()==z3.sat)==expected
            solver.pop()
        if mode=='dag':
            solver.add(z3.Xor(direct,compressed)); assert solver.check()==z3.unsat
