import importlib.util
from itertools import product
from pathlib import Path
import random

import pytest
import z3
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.dictionary_encoding import membership


def reference():
    spec=importlib.util.spec_from_file_location('dictionary_equality_reference',Path('experiments/results/equality-reuse/reference_dictionary_encoding.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.membership


def test_random_formulas_preserve_exact_ast_and_equivalence():
    rng=random.Random(4201);alphabet=Alphabet(('a','b','et'));old=reference()
    words=[w for n in range(1,4) for w in product(alphabet.symbols,repeat=n)]
    for case in range(50):
        candidates=tuple(rng.sample(words,rng.randrange(0,15)))
        slots=max(map(len,candidates),default=0)+rng.randrange(3)
        symbols=[z3.Int(f'reuse_{case}_{i}') for i in range(slots)];size=z3.Int(f'reuse_size_{case}')
        before=old(candidates,symbols,size,alphabet);after=membership(candidates,symbols,size,alphabet)
        assert before.eq(after)
        solver=z3.Solver();solver.add(z3.Xor(before,after));assert solver.check()==z3.unsat


def test_cache_is_local_to_formula_variables_and_contexts():
    alphabet=Alphabet(('a','b'));words=(('a',),('b',),('a','b'))
    old=reference()
    for context in (z3.Context(),z3.Context()):
        for label in ('first','second'):
            symbols=[z3.Int(label+str(i),ctx=context) for i in range(3)]
            size=z3.Int(label+'size',ctx=context)
            assert membership(words,symbols,size,alphabet).eq(old(words,symbols,size,alphabet))


def test_invalid_token_still_raises_value_error():
    with pytest.raises(ValueError):membership((('invalid',),),[z3.Int('reuse_invalid')],z3.Int('reuse_invalid_size'),Alphabet(('a',)))
