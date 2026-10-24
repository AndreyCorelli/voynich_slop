from itertools import product
import z3
from benchmarks.latin_h2_identifiability import select_family, encrypt, mapping_solver


def test_nested_training_cipher_and_fresh_novel_holdouts():
    pool=[''.join(value) for value in product('abc',repeat=4)]
    types,held=select_family(pool,7401,7501)
    assert len(types)==24 and len(set(types))==24 and len(held)==6
    assert not set(types)&set(held)
    key={'a':['aa','ab'],'b':['ba','bb'],'c':['ca','cb']}
    previous=[]; prior_held=None
    for n in (12,18,24):
        train=[word for word in types[:n] for _ in range(2)]
        cipher,held_cipher=encrypt(train,held,key)
        assert cipher[:len(previous)]==previous
        assert prior_held is None or held_cipher==prior_held
        observed={code for word in cipher for code in word}
        assert all(code in observed for word in held_cipher for code in word)
        previous=cipher; prior_held=held_cipher


def test_excluding_first_observed_key_detects_uniqueness_and_ambiguity():
    cipher=['xy']; domains={'x':set('ab'),'y':set('ab')}; first={'x':'a','y':'b'}
    solver,_=mapping_solver(cipher,[['ab']],domains,'ab',2,1000,first)
    assert solver.check()==z3.unsat
    solver,eq=mapping_solver(cipher,[['ab','ba']],domains,'ab',2,1000,first)
    assert solver.check()==z3.sat
    assert z3.is_true(solver.model().eval(eq['x','b']))
