"""Within-word randomized code renaming preserving equality and code counts."""
from collections import Counter
import random


def pattern_preserving_shuffle(words, seed):
    rng = random.Random(seed); shuffled = []
    for word in words:
        counts = Counter(word); mapping = {}
        for frequency in sorted(set(counts.values())):
            codes = sorted(code for code, count in counts.items() if count == frequency)
            targets = list(codes); rng.shuffle(targets)
            mapping.update(zip(codes, targets))
        shuffled.append([mapping[code] for code in word])
    return shuffled
