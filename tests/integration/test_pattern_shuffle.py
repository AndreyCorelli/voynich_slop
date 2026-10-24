from collections import Counter
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.language.word_patterns import equality_pattern


def test_exact_pattern_and_per_word_counts_preserved():
    words = [list('abcdef'), list('abacdc'), list('aaaa'), list('abbccc')]
    shuffled = pattern_preserving_shuffle(words, 5004)
    assert shuffled != words and shuffled == pattern_preserving_shuffle(words, 5004)
    for original, randomized in zip(words, shuffled):
        assert Counter(original) == Counter(randomized)
        assert equality_pattern(original) == equality_pattern(randomized)
    assert shuffled[-2:] == words[-2:]
