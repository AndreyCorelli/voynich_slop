from voynich_smt.government_context import features

def test_center_word_pos_finiteness_masked():
    a=features(['ad','x','est'],['ADP','NOUN','VERB'],[0,0,.95],1,True)
    b=features(['ad','SECRET','est'],['ADP','ADV','VERB'],[0,1,.95],1,True)
    assert a==b and not any('SECRET' in x for x in b)

def test_geometry_does_not_read_anchor_identity():
    assert features(['ad','x'],['ADP','NOUN'],[0,0],1)==features(['cum','x'],['ADP','NOUN'],[0,0],1)

def test_identity_arm_adds_only_predicted_marker_words():
    a=features(['ad','x','amicus'],['ADP','NOUN','NOUN'],[0,0,0],1,True)
    assert any('word=ad' in f for f in a)
    assert not any('amicus' in f or 'word=x' in f for f in a)

def test_finite_threshold_and_nearest_distance():
    a=features(['x','a','b'],['NOUN','VERB','VERB'],[0,.4,.95],0)
    assert 'right:finite:distance=2' in a
    assert 'right:finite:confidence=high' in a

def test_government_radius_is_bounded():
    a=features(['ad']+['x']*9,['ADP']+['NOUN']*9,[0]*10,9)
    assert 'left:adp:NONE' in a
