from benchmarks.manuscript_character_replication import extract


def records(n,folio='a'):
    return [{'folio':folio,'tokens':['a'],'excluded_reason':None,'word_in_locus':i,'locus':'x','physical_line':1} for i in range(n)]


def test_excluded_folios_and_invalid_words_are_barriers():
    raw=records(31)+[{**records(1)[0],'excluded_reason':'uncertain'}]+records(32)+records(32,'excluded')
    blocks=extract(raw,{'excluded'}); assert set(blocks)=={'a'} and len(blocks['a'])==1
    assert blocks['a'][0]['start']==32 and blocks['a'][0]['end_exclusive']==64


def test_folio_boundary_is_not_bridged():
    assert extract(records(31)+records(31,'b'),set())=={}


def test_blocks_are_nonoverlapping_with_raw_layout_identity():
    blocks=extract(records(65),set())['a']; assert [(b['start'],b['end_exclusive']) for b in blocks]==[(0,32),(32,64)]
    assert blocks[1]['positions']==list(range(32,64)) and set(blocks[1]['line_ids'])=={'a:x:1'}
