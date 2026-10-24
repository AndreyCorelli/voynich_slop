from benchmarks.multilingual_character import blocks32, assign, eight_lines


def test_barriers_and_segment_boundaries_are_not_bridged():
    blocks,stats=blocks32([['a']*31+[None]+['b']*32,['c']*31,['d']*32])
    assert len(blocks)==2 and all(w==['b'] for w in blocks[0]['words'])
    assert all(w==['d'] for w in blocks[1]['words'])
    assert stats['barrier_or_nonascii_slots']==1


def test_nonascii_is_a_barrier_not_a_dropped_token():
    blocks,stats=blocks32([['a']*31+['ł']+['b']*32])
    assert len(blocks)==1 and all(w==['b'] for w in blocks[0]['words']) and stats['barrier_or_nonascii_slots']==1


def test_layout_sensitivity_keeps_words_and_source_identity():
    source,_=blocks32([['ab']*32]); template=[{'folio':'a','start':123,'words':[['z']]*32,'positions':[4]*32,'line_ids':['line']*32}]
    b=assign(template,source); layout=eight_lines(b)
    assert layout[0]['words']==b[0]['words'] and layout[0]['source_slots']==b[0]['source_slots']
    assert layout[0]['positions']==list(range(8))*4 and len(set(layout[0]['line_ids']))==4
    assert b[0]['positions']==[4]*32
