"""Exact equality-pattern subsets for injective fixed-boundary substitution."""

def equality_pattern(symbols):
    seen = {}
    return tuple(seen.setdefault(symbol, len(seen)) for symbol in symbols)


def pattern_subsets(words, patterns):
    patterns = set(patterns)
    lengths = {len(pattern) for pattern in patterns}
    subsets = {pattern: [] for pattern in patterns}
    for word in words:
        if len(word) in lengths:
            pattern = equality_pattern(word)
            if pattern in subsets: subsets[pattern].append(word)
    return subsets
