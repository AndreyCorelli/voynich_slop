from itertools import product
from collections import Counter
from voynich_smt.language.homophone_patterns import compatible, homophone_subsets


def test_weak_patterns_allow_homophones_but_preserve_repeated_code_consistency():
    assert compatible((0,1,2), 'aba', 2)
    assert not compatible((0,1,2), 'aba', 1)
    assert not compatible((0,1,0), 'abc', 2)
    assert not compatible((0,1,2), 'aaa', 2)
    assert homophone_subsets(['aaa','aba','abc'], [(0,1,2)], 2) == {(0,1,2): ['aba','abc']}


def test_local_filter_matches_exhaustive_bounded_mapping():
    for pattern in product(range(3), repeat=3):
        codes = sorted(set(pattern))
        for word in map(''.join, product('ab', repeat=3)):
            expected = any(''.join(mapping[c] for c in pattern) == word and
                           max(Counter(mapping.values()).values()) <= 2
                           for values in product('ab', repeat=len(codes))
                           for mapping in [dict(zip(codes, values))])
            assert compatible(pattern, word, 2) == expected
