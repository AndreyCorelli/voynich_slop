"""Sound local candidate filtering with bounded many-code-to-letter mappings."""
from voynich_smt.language.word_patterns import equality_pattern


def compatible(pattern, word, max_homophones=2):
    if len(pattern) != len(word): return False
    mapping = {}; inverse = {}
    for code, letter in zip(pattern, word):
        if code in mapping and mapping[code] != letter: return False
        mapping[code] = letter
        inverse.setdefault(letter, set()).add(code)
        if len(inverse[letter]) > max_homophones: return False
    return True


def homophone_subsets(words, patterns, max_homophones=2):
    patterns = set(patterns); by_length = {}
    for pattern in patterns: by_length.setdefault(len(pattern), []).append(pattern)
    subsets = {pattern: [] for pattern in patterns}
    for word in words:
        for pattern in by_length.get(len(word), []):
            if compatible(pattern, word, max_homophones): subsets[pattern].append(word)
    return subsets
