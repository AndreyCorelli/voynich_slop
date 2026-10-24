"""Exact Boolean-map membership in a minimized finite word automaton."""
import z3
from voynich_smt.language.word_automaton import WordAutomaton
from voynich_smt.solver.layered_membership import layered_membership
from voynich_smt.models.alphabet import Alphabet


def compressed_membership(cipher, candidates, equalities, namespace, mode='dag'):
    if any(len(word) != len(cipher) for word in candidates): raise ValueError('candidate length mismatch')
    candidates = [word for word in candidates if all(word[i] == word[j] for i in range(len(cipher)) for j in range(i) if cipher[i] == cipher[j])]
    if not candidates: return z3.BoolVal(False)
    a = WordAutomaton.from_sorted(sorted(set(candidates)))
    alphabet = sorted({letter for _, letter in equalities})
    if mode == 'layered':
        symbols = [z3.Sum([z3.If(equalities[(code, letter)], i, 0) for i, letter in enumerate(alphabet)]) for code in cipher]
        return layered_membership(a, Alphabet(tuple(alphabet)), symbols, namespace)[0]
    if mode not in ('dag', 'defined'): raise ValueError(mode)
    cache = {}; definitions = []
    def visit(state, depth):
        identity = (state, depth)
        if identity in cache: return cache[identity]
        terminal, edges = a.states[state]
        if depth == len(cipher): result = z3.BoolVal(terminal)
        else:
            result = z3.Or([z3.And(equalities[(cipher[depth], letter)], visit(child, depth+1)) for letter, child in edges])
        if mode == 'defined' and depth < len(cipher):
            variable = z3.Bool(f'{namespace}_node_{state}_{depth}')
            definitions.append(variable == result); result = variable
        cache[identity] = result
        return result
    root = visit(a.root, 0)
    return z3.And(root, *definitions)
