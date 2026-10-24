from itertools import product
import pytest
import z3
from voynich_smt.solver.selection import constrain_state


def test_state_recurrence_matches_history_with_padding_and_single_homophones():
    states = {}
    solver = z3.Solver()
    counts = [z3.Int('count_a'), z3.Int('count_b')]
    solver.add(*[z3.And(c >= 1, c <= 2) for c in counts])
    history = []
    mismatches = []
    for i in range(5):
        token, choice = z3.Int(f'token_{i}'), z3.Int(f'choice_{i}')
        active = z3.Bool(f'active_{i}')
        solver.add(z3.If(active, z3.And(token >= 0, token < 2), token == 2))
        constrain_state(solver, token, choice, active, counts, states, {0, 1}, i)
        for p in range(2):
            occurrences = z3.Sum([z3.If(t == p, 1, 0) for t in history]) if history else z3.IntVal(0)
            expected = z3.If(counts[p] == 1, 0, occurrences % 2)
            mismatches.append(z3.And(active, token == p, choice != expected))
            mismatches.append(states[p] != (z3.Sum([z3.If(t == p, 1, 0) for t in history + [token]]) % 2 == 1))
        history.append(token)
    solver.add(z3.Or(mismatches))
    assert solver.check() == z3.unsat


@pytest.mark.parametrize('reset', ['word', 'text'])
def test_state_and_history_hidden_recovery_agree(reset):
    from voynich_smt.cipher.base import Bounds
    from voynich_smt.language.dictionary import WordDictionary
    from voynich_smt.models.alphabet import Alphabet
    from voynich_smt.models.settings import HomophoneSelection
    from voynich_smt.models.text import Text
    from voynich_smt.solver.recovery import _recover
    for word in product('xy', repeat=3):
        arguments = dict(plaintext=None, ciphertext=Text((word, ('x',))),
            plain_alphabet=Alphabet(tuple('ab')), cipher_alphabet=Alphabet(tuple('xy')),
            bounds=Bounds('verbose', 2, 1, 2), timeout_ms=3000,
            dictionary=WordDictionary.from_strings(('a','ab','ba','aba','bbb')),
            min_word_length=1, max_word_length=3, selection=HomophoneSelection('cycle', reset),
            dictionary_encoding='trie')
        old = _recover(**arguments, cycle_encoding='history')
        new = _recover(**arguments, cycle_encoding='state')
        assert old.status == new.status and old.status != 'UNKNOWN'
        assert new.status != 'SAT' or new.verified


def test_auto_selects_state_only_for_h2_cycles():
    from voynich_smt.cipher.base import Bounds
    from voynich_smt.models.alphabet import Alphabet
    from voynich_smt.models.settings import HomophoneSelection
    from voynich_smt.models.text import Text
    from voynich_smt.solver.recovery import recover, _recover
    args = (Text.from_string('a'), Text.from_string('x'), Alphabet(('a',)), Alphabet(tuple('xyz')))
    assert recover(*args, Bounds('verbose',2,1,2), selection=HomophoneSelection('cycle')).capacity['cycle_encoding'] == 'state'
    assert recover(*args, Bounds('verbose',3,1,2), selection=HomophoneSelection('cycle')).capacity['cycle_encoding'] == 'history'
    assert recover(*args, Bounds('verbose',2,1,2)).capacity['cycle_encoding'] == 'history'
    with pytest.raises(ValueError): _recover(*args, Bounds('verbose',3,1,2),1000,cycle_encoding='state')
