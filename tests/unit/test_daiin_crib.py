from benchmarks.daiin_crib import alignments, compatible, solve_family


def test_crib_enumerates_only_prefix_free_segmentations():
    keys = list(alignments('vnd', 'daiin'))
    assert len(keys) == 5
    assert {'v': 'd', 'n': 'ai', 'd': 'in'} in keys
    assert {'v': 'da', 'n': 'i', 'd': 'in'} not in keys


def test_repeated_plaintext_letter_requires_same_code():
    assert list(alignments('nn', 'aiai', {'n': 'ai'})) == [{'n': 'ai'}]
    assert not list(alignments('nn', 'aiin', {'n': 'ai'}))


def test_joint_family_can_fail_despite_individual_support():
    # v=d, n=ai, d=in. 'von' forces o=x, 'vor' forces o=y.
    from collections import Counter
    result = solve_family(Counter({'daiin': 1, 'dxai': 1, 'dyz': 1}),
                          'vnd', ['von', 'vor'], 3000)
    assert result['proved_maximum_simultaneous_targets'] == 1
    assert result['witness']['independently_verified']
    assert compatible(result['witness']['key'])


def test_final_letter_obstruction_is_independent_of_code_bound():
    from benchmarks.daiin_crib import final_letter_obstruction
    assert final_letter_obstruction({'n': 3, 'iin': 1, 'daiin': 4}) == {
        'n': [], 'in': [], 'iin': []}
    assert final_letter_obstruction({'inal': 1})['in'] == ['inal']
