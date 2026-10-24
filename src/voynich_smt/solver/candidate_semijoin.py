"""Sound pairwise support pruning on shared cipher-code assignments."""
from voynich_smt.solver.capacity_matching import propagate_candidates as capacity_propagation


def semijoin(cipher_words, candidates):
    remaining = [list(words) for words in candidates]
    positions = [{code: cipher.index(code) for code in cipher} for cipher in cipher_words]
    pairs = []
    for i in range(len(positions)):
        for j in range(i):
            shared = sorted(positions[i].keys() & positions[j].keys())
            if len(shared) >= 2:
                pairs.append((i, j, tuple(positions[i][c] for c in shared), tuple(positions[j][c] for c in shared)))
    rounds = 0
    while True:
        rounds += 1; changed = False
        for i, j, left, right in pairs:
            def signature(word, indices): return tuple(word[k] for k in indices)
            supported = {signature(word, right) for word in remaining[j]}
            kept = [word for word in remaining[i] if signature(word, left) in supported]
            changed |= len(kept) != len(remaining[i]); remaining[i] = kept
            supported = {signature(word, left) for word in kept}
            kept = [word for word in remaining[j] if signature(word, right) in supported]
            changed |= len(kept) != len(remaining[j]); remaining[j] = kept
            if not remaining[i] or not remaining[j]: return remaining, rounds, True
        if not changed: return remaining, rounds, False


def propagate_candidates(cipher_words, candidates, alphabet, capacity=2):
    remaining = [list(words) for words in candidates]; rounds = 0
    while True:
        before = list(map(len, remaining))
        remaining, domains, count, contradiction = capacity_propagation(cipher_words, remaining, alphabet, capacity)
        rounds += count
        if contradiction: return remaining, domains, rounds, True
        remaining, count, contradiction = semijoin(cipher_words, remaining)
        rounds += count
        if contradiction: return remaining, domains, rounds, True
        if before == list(map(len, remaining)): return remaining, domains, rounds, False
