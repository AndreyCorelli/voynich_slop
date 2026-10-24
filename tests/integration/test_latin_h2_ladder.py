from benchmarks.latin_h2_ladder import nested_words


def test_nested_independent_extension_retains_pool():
    pool = ['aaa', 'bbb']
    eligible = ['aaa', 'bbb', 'ccc', 'ddd', 'eee', 'fff']
    rungs = nested_words(pool, eligible, (2, 3, 6))
    assert list(map(len, rungs)) == [2, 3, 6]
    assert set(rungs[0]) <= set(rungs[1]) <= set(rungs[2])
    assert rungs == nested_words(list(reversed(pool)), list(reversed(eligible)), (2, 3, 6))
    assert rungs[-1] == sorted(eligible)
