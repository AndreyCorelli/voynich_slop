from voynich_smt.opaque_neighbor_features import features


def public():
    return [dict(sent_id=str(i),tokens=[dict(id=w,anchor='PRIVATE',tag='PRIVATE') for w in words]) for i,words in enumerate([['a','x','b'],['a','x','b'],['b','x','a']])]


def test_features_are_invariant_to_id_renaming_and_private_fields():
    p=public();q=[dict(s,tokens=[dict(id={'a':'Q','x':'R','b':'S'}[t['id']],anchor=None,tag='X') for t in s['tokens']]) for s in p]
    assert features(p)==features(q)
    assert features(p,False)==features(q,False)


def test_boundaries_and_repeated_pairs_are_sentence_local():
    rows=features(public())
    assert len(rows)==9
    assert 'opaque:left:edge' in rows[0]
    assert 'opaque:right:edge' in rows[2]
    assert 'opaque:left:pairrepeat:True' in rows[1]
    assert 'opaque:left:pairrepeat:False' in rows[7]
    assert not any('pairrepeat' in f for f in features(public(),False)[1])


def test_empty_input():
    assert features([])==[]
