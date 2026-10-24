from voynich_smt.anchor_challenge import challenge_patterns


def test_challenge_uses_fit_frequency_and_excludes_rehearsed_pair():
    anchors={'in':'ADP','et':'CCONJ','a':'ADP','b':'ADP','c':'ADP','x':'CCONJ','y':'CCONJ','z':'CCONJ'}
    sentences=[{'tokens':[{'word':w} for w in ['in']*20+['et']*20+['b']*3+['a']*2+['c']+['y']*3+['x']*2+['z']]}]
    p=challenge_patterns(sentences,anchors)
    assert len(p)==8
    assert p['unseen_b_y']=={'b':'y','y':'b'}
    assert p['same_adp']=={'b':'a','a':'b'}
    assert p['same_conjunction']=={'y':'x','x':'y'}
    for name,mapping in p.items():
        if name.startswith('unseen_'):
            assert not set(mapping)&{'in','et'}
            assert set(mapping)==set(mapping.values())
            assert len({anchors[w] for w in mapping})==2
