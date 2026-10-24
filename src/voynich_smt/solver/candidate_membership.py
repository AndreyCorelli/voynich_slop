"""Direct exact finite candidate relations over shared code-decoding variables."""
import z3


def candidate_membership(letters, cipher, candidates, equalities):
    rows = []
    for word in candidates:
        if len(word) != len(cipher): raise ValueError('Candidate length mismatch')
        assignments = dict(zip(cipher, word))
        if any(assignments[code] != letter for code,letter in zip(cipher,word)): continue
        rows.append(z3.And([equalities[(code, letter)] for code,letter in assignments.items()]))
    return z3.Or(rows)
