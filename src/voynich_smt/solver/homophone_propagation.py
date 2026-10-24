"""Sound finite-domain support pruning for fixed-boundary bounded homophones."""
from collections import Counter


def propagate_candidates(cipher_words, candidates, alphabet, capacity=2):
    domains = {code: set(alphabet) for word in cipher_words for code in word}
    remaining = [list(words) for words in candidates]
    rounds = 0
    while True:
        rounds += 1; changed = False
        for index, cipher in enumerate(cipher_words):
            kept = [word for word in remaining[index]
                    if all(letter in domains[code] for code,letter in zip(cipher,word))]
            if not kept: return remaining, domains, rounds, True
            if len(kept) != len(remaining[index]): changed = True
            remaining[index] = kept
            for code in dict.fromkeys(cipher):
                position = cipher.index(code)
                supported = {word[position] for word in kept}
                reduced = domains[code] & supported
                if not reduced: return remaining, domains, rounds, True
                if reduced != domains[code]: changed = True; domains[code] = reduced
        forced = Counter(next(iter(domain)) for domain in domains.values() if len(domain) == 1)
        if any(count > capacity for count in forced.values()): return remaining, domains, rounds, True
        full = {letter for letter,count in forced.items() if count == capacity}
        for code, domain in domains.items():
            if len(domain) > 1:
                reduced = domain - full
                if not reduced: return remaining, domains, rounds, True
                if reduced != domain: changed = True; domains[code] = reduced
        if not changed: return remaining, domains, rounds, False
