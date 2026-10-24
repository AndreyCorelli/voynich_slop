from benchmarks.word_repetition import metrics,pattern,windows,compare,summarize


def test_all_pair_distances_and_multiplicities():
    m=metrics(('a','b','a','a','b','c'))
    assert m['distinct_words']==3 and m['repeat_excess']==3
    assert m['repeated_types']==2 and m['max_multiplicity']==3
    assert m['equal_word_pairs']==4
    assert m['pair_distance_histogram']=={1:1,2:1,3:2}
    assert m['multiplicity_histogram']=={1:1,2:1,3:1}
    assert m['nearest_repeat_distance']==1
    assert metrics(tuple('abc'))['nearest_repeat_distance'] is None


def test_nonoverlap_restarts_at_gaps_and_segments():
    result=list(windows([['a']*45+[None]+['b']*22,['c']*21]))
    assert len(result)==25
    assert sum(non for _,non in result)==3
    assert all(len(set(w))==1 for w,_ in result)


def test_cipher_equality_implication_does_not_require_exact_partition():
    target=tuple(['a','a']+[f'x{i}' for i in range(20)])
    row=compare([['b']*22],{'test':target})
    c=row['comparisons'][0]
    assert c['equal_ciphertext_implies_equal_plaintext_matches']==1
    assert c['exact_equality_partition_matches']==0
    assert c['marginal_ranks']['distinct_words']=={'below':1,'equal':0,'above':0}
    assert row['nonoverlapping_windows']==1


def test_no_repeat_target_has_vacuous_implication_but_informative_exact_partition():
    target=tuple(f'x{i}' for i in range(22))
    row=compare([['a']*23],{'test':target})
    c=row['comparisons'][0]
    assert row['windows']==c['equal_ciphertext_implies_equal_plaintext_matches']==2
    assert c['fraction']==1 and c['exact_equality_partition_matches']==0
    assert pattern(('a','b','a'))==pattern(('x','y','x'))==(0,1,0)


def test_quantiles_from_histograms():
    assert summarize({1:1,3:1})['median']==2
    assert summarize({})=={'windows':0}
