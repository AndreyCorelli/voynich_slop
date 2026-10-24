from itertools import permutations
from voynich_smt.language.word_patterns import equality_pattern, pattern_subsets


def test_patterns_exact_under_injective_renaming():
    for word in ['aba', 'abb', 'abc', 'aaaa']:
        for rename in permutations('xyz'):
            key = dict(zip('abc', rename))
            assert equality_pattern(word) == equality_pattern([key[c] for c in word])
    assert equality_pattern('aba') != equality_pattern('abb')
    assert equality_pattern('abc') != equality_pattern('aba')
    subsets = pattern_subsets(['aba','abb','abc','xyx','xyz'], [(0,1,0), (0,1,2), (0,0)])
    assert subsets == {(0,1,0): ['aba','xyx'], (0,1,2): ['abc','xyz'], (0,0): []}
