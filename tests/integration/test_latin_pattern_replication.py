from itertools import product
from benchmarks.latin_pattern_replication import select_fixture


def test_selection_is_reproducible_novel_and_code_covered():
    eligible = [''.join(chars) for chars in product('abcd', repeat=5)]
    first = select_fixture(eligible, 5101); second = select_fixture(eligible, 5102)
    assert first == select_fixture(eligible, 5101) and first != second
    for train, held in (first, second):
        assert len(train) == len(set(train)) == 12 and len(held) == len(set(held)) == 3
        assert not set(train) & set(held)
        assert set(''.join(held)) <= set(''.join(train))
