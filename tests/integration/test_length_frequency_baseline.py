from benchmarks import length_frequency_baseline as b


def test_fixed_ratio_frequency_and_lexical_ties():
    # Ratio two; same-length choices favor frequency, then lexical spelling.
    training=['ab','ba','ba'];cipher=['xxxx']*3
    p=b.predict(training,cipher,['aa','ab','ba','aaa'],['yyyy','yyyyyy'])
    assert p['predicted_words']==[tuple('ba'),tuple('aaa')]
    assert b.predict(['ab','ba'],['xxxx']*2,['aa','ab','ba'],['yyyy'])['predicted_words']==[tuple('ab')]
    # Glyph identities are irrelevant; neither key nor holdout truth is an input.
    assert p==b.predict(training,['zzzz']*3,['aa','ab','ba','aaa'],['zzzz','zzzzzz'])


def test_unresolved_and_controls_not_scored_as_accuracy():
    positive={'id':'p','group':'g','kind':'positive','baseline':{'predicted_words':[['a']]},'request':{'dictionary':{'words':[['a']]}},'training_plaintext':[['b']],'holdout_plaintext':{'words':[['a']]},'saved_solver':{'result':{'status':'UNKNOWN'}}}
    r=b.evaluate(positive)
    assert r['baseline_exact']==1 and 'key_exact' not in r
    control=dict(positive,kind='shuffle',holdout_plaintext=None)
    r=b.evaluate(control)
    assert 'baseline_exact' not in r and 'key_exact' not in r
