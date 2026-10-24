from itertools import product
import pytest
import z3
from voynich_smt.language.word_automaton import WordAutomaton
from voynich_smt.solver.automaton_membership import AutomatonMembership
from voynich_smt.models.alphabet import Alphabet


def test_exact_language_count_and_suffix_sharing():
    words=['a','ab','ac','ba','bb','bc']
    a=WordAutomaton.from_sorted(words)
    assert a.accepted_word_count()==len(words)
    for n in range(5):
        for chars in product('abc',repeat=n):assert a.accepts(chars)==(''.join(chars) in words)
    assert len(a.states)<sum(map(len,words))
    for invalid in ([],[''],['b','a'],['a','a']):
        with pytest.raises(ValueError):WordAutomaton.from_sorted(invalid)


def test_symbolic_membership_padding_and_exact_equivalence():
    words=['a','ab','ba'];alphabet=Alphabet(tuple('ab'));a=WordAutomaton.from_sorted(words)
    table=AutomatonMembership(a,alphabet);symbols=z3.Ints('slot0 slot1 slot2');size=z3.Int('size')
    formula=table.membership(symbols,size)
    flat=z3.Or([z3.And(size==len(w),*[s==(alphabet.index(w[i]) if i<len(w) else 2) for i,s in enumerate(symbols)]) for w in words])
    solver=z3.Solver();solver.add(z3.Xor(formula,flat));assert solver.check()==z3.unsat
    solver=z3.Solver();solver.add(formula,size==2,symbols[0]==0);assert solver.check()==z3.sat
    assert solver.model().eval(symbols[1]).as_long()==1 and solver.model().eval(symbols[2]).as_long()==2
