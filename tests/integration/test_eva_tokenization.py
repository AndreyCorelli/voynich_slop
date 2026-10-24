import pytest

from benchmarks.eva_tokenization import grouped_word, repetition_pairs, screen


def test_longest_grouping_round_trip_and_no_other_merges():
    source=tuple('chshcthckhcphcfhqoaiin')
    result=grouped_word(source)
    assert result==('ch','sh','cth','ckh','cph','cfh','q','o','a','i','i','n')
    assert ''.join(result)==''.join(source)
    with pytest.raises(ValueError):grouped_word(('ch',))
    with pytest.raises(ValueError):grouped_word(tuple('Ch'))


def test_boundaries_and_word_equality_preserved():
    atomic=tuple(map(tuple,('chor','c','h','chor','cthor')))
    grouped=tuple(grouped_word(w) for w in atomic)
    assert repetition_pairs(atomic)==repetition_pairs(grouped)==[(0,3)]
    assert grouped[1:3]==(('c',),('h',))


def test_grouping_can_remove_too_short_failure_but_add_too_long_failure():
    atomic=(tuple('chch'),);grouped=(grouped_word(atomic[0]),)
    assert screen([['a']],atomic)['positionwise_length_compatible']==0
    assert screen([['a']],grouped)['positionwise_length_compatible']==1
    assert screen([['abcd']],atomic)['positionwise_length_compatible']==1
    assert screen([['abcd']],grouped)['positionwise_length_compatible']==0


def test_gap_and_reversible_contraction_repetition_filter():
    cipher=(('ch',),('ch',))
    rules=[{'id':'ae','expansion':'ae','position':'any'}]
    r=screen([['ae','ae',None,'ae','a']],cipher,rules)
    assert r['windows']==2
    assert r['positionwise_length_compatible']==2
    assert r['repetition_compatible']==r['length_and_repetition_compatible']==1
