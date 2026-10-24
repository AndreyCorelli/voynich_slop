"""Cycle constraints use only constant divisors and count active plaintext tokens."""

import z3


def constrain(solver, selection, token, choice, active, counts, history, ids, max_homophones):
    if selection.mode == "free":
        return
    for p in sorted(ids):
        occurrences = z3.Sum([z3.If(previous == p, 1, 0) for previous in history]) if history else z3.IntVal(0)
        for count in range(1, max_homophones + 1):
            solver.add(z3.Implies(z3.And(active, token == p, counts[p] == count),
                                  choice == (0 if count == 1 else occurrences % count)))


def constrain_state(solver, token, choice, active, counts, states, ids, position):
    """H2 cycle phase as a Boolean recurrence, including inactive padding.

    Each letter toggles only on its own active appearance. Unlike summing the
    entire symbolic history, each update refers to just its previous phase.
    """
    for p in sorted(ids):
        phase = states.get(p, z3.BoolVal(False))
        present = z3.And(active, token == p)
        solver.add(z3.Implies(present,
            choice == z3.If(z3.And(counts[p] == 2, phase), 1, 0)))
        following = z3.Bool(f'cycle_phase_{position}_{p}')
        solver.add(following == z3.Xor(phase, present))
        states[p] = following
