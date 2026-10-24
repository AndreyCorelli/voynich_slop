"""Sound global capacity support filtering using bipartite matching."""
from voynich_smt.solver.homophone_propagation import propagate_candidates as local_propagation


def feasible(domains, capacity, forced=None):
    occupied = {}
    codes = sorted(domains, key=lambda c: (len(domains[c]), str(c)))
    if forced is not None:
        code, letter = forced
        if letter not in domains[code]: return False
        occupied[(letter, 0)] = code
        codes.remove(code)
    def augment(code, seen):
        for letter in sorted(domains[code]):
            for slot in range(capacity):
                target = (letter, slot)
                if target in seen: continue
                seen.add(target)
                owner = occupied.get(target)
                if forced is not None and owner == forced[0]: continue
                if owner is None or augment(owner, seen):
                    occupied[target] = code
                    return True
        return False
    return all(augment(code, set()) for code in codes)


def supported_domains(domains, capacity):
    if not feasible(domains, capacity): return {}, True
    return {code: {letter for letter in domain if feasible(domains, capacity, (code, letter))}
            for code, domain in domains.items()}, False


def propagate_candidates(cipher_words, candidates, alphabet, capacity=2):
    remaining = [list(words) for words in candidates]
    rounds = 0
    while True:
        remaining, domains, local_rounds, contradiction = local_propagation(cipher_words, remaining, alphabet, capacity)
        rounds += local_rounds
        if contradiction: return remaining, domains, rounds, True
        supported, contradiction = supported_domains(domains, capacity)
        if contradiction: return remaining, domains, rounds, True
        if supported == domains: return remaining, domains, rounds, False
        reduced = [[word for word in words if all(letter in supported[code] for code, letter in zip(cipher, word))]
                   for cipher, words in zip(cipher_words, remaining)]
        if any(not words for words in reduced): return reduced, supported, rounds, True
        remaining = reduced
