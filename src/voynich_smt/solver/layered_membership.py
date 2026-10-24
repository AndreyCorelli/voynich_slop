"""Exact fixed-length membership through sparse, viable automaton layers."""
import z3


def layered_membership(automaton, alphabet, symbols, namespace):
    length = len(symbols)
    # Can a state reach a terminal after exactly r transitions?
    viable = [{i for i, (terminal, _) in enumerate(automaton.states) if terminal}]
    for _ in range(length):
        previous = viable[-1]
        viable.append({i for i, (_, edges) in enumerate(automaton.states)
                       if any(child in previous for _, child in edges)})
    states = [z3.Int(f'{namespace}_state_{i}') for i in range(length + 1)]
    constraints = [states[0] == automaton.root]
    reachable = {automaton.root} if automaton.root in viable[length] else set()
    edge_counts = []
    for depth, symbol in enumerate(symbols):
        edges = [(parent, alphabet.index(letter), child)
                 for parent in sorted(reachable)
                 for letter, child in automaton.states[parent][1]
                 if child in viable[length - depth - 1]]
        constraints.append(z3.Or([z3.And(states[depth] == parent, symbol == letter,
                                        states[depth + 1] == child)
                                  for parent, letter, child in edges]))
        reachable = {child for _, _, child in edges}
        edge_counts.append(len(edges))
    constraints.append(z3.Or([states[-1] == state for state in sorted(reachable)
                              if automaton.states[state][0]]))
    return z3.And(constraints), states, edge_counts
