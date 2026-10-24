from benchmarks.context_prediction import fit, probability, score, UNK


def block(seq): return {'words':[list(w) for w in seq],'folio':'a','start':0}


def test_probability_normalization_and_unknown_mass():
    m=fit([block(['a','b','a','b','c'])],'word',10)
    assert 'c' not in m['vocabulary'] and UNK in m['vocabulary']
    for previous in (None,'a','never'):
        assert abs(sum(probability(w,previous,m) for w in m['vocabulary'])-1)<1e-10
        assert probability('never',previous,m)==probability(UNK,previous,m)>0


def test_synthetic_order_positive_and_iid_shuffle_negative():
    train=[block(['a','b']*50)]
    model=fit(train,'word',10); unigram=fit(train)
    held=block(['a','b']*20)
    assert score(held,model)['bits_per_token']<score(held,unigram)['bits_per_token']
    grouped=block(['a']*20+['b']*20)
    assert score(grouped,model)['bits_per_token']>score(grouped,unigram)['bits_per_token']


def test_suffix_context_uses_previous_word_and_not_target():
    model=fit([block(['ax','a','ax','a','by','b','by','b'])],'suffix1',10)
    assert probability('a','cx',model)>probability('a','cy',model)


def test_no_transition_across_block_boundary():
    model=fit([block(['a','a']),block(['b','b'])],'word',10)
    assert model['pairs'].get('a',{}).get('b',0)==0


def test_interpolation_against_hand_computed_probability():
    model=fit([block(['a','b','a','b'])],'word',10,.5)
    # Base P(b)=5/11; contextual P(b|a)=6/11; half mixture =1/2.
    assert abs(probability('b','a',model)-.5)<1e-12
    assert abs(probability('b',None,model)-5/11)<1e-12
