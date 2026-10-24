from itertools import product
import z3
from voynich_smt.language.word_automaton import WordAutomaton
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.layered_membership import layered_membership


def test_symbolic_language_equivalence_including_impossible_lengths():
    words = ['a', 'ab', 'aba', 'ba', 'bb']
    a = WordAutomaton.from_sorted(words); alphabet = Alphabet(tuple('ab'))
    for length in range(5):
        symbols = [z3.Int(f'letter_{length}_{i}') for i in range(length)]
        formula, states, _ = layered_membership(a, alphabet, symbols, f'query_{length}')
        flat = z3.Or([z3.And([s == alphabet.index(c) for s, c in zip(symbols, word)])
                      for word in words if len(word) == length])
        solver = z3.Solver()
        # The path states are witnesses, so quantify them when comparing languages.
        solver.add(z3.Xor(z3.Exists(states, formula), flat))
        assert solver.check() == z3.unsat


def test_invalid_letters_cannot_use_missing_transitions():
    a = WordAutomaton.from_sorted(['ab']); alphabet = Alphabet(tuple('ab'))
    symbols = z3.Ints('x y'); formula, _, edges = layered_membership(a, alphabet, symbols, 'invalid')
    solver = z3.Solver(); solver.add(formula, symbols[0] == 2)
    assert solver.check() == z3.unsat and edges == [1, 1]
