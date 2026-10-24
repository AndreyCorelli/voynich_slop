"""Concrete selection rules used for generation and independent verification."""

from collections import Counter
import random


def choose(plaintext, encoder, selection, seed=0):
    rng, occurrences, result = random.Random(seed), Counter(), []
    for word in plaintext.words:
        if selection.reset == "word":
            occurrences.clear()
        for symbol in word:
            count = len(encoder.codebook[symbol])
            result.append(rng.randrange(count) if selection.mode == "free" else occurrences[symbol] % count)
            occurrences[symbol] += 1
    return tuple(result)


def accepts(plaintext, encoder, choices, selection):
    return selection.mode == "free" or choices == choose(plaintext, encoder, selection)
