from voynich_smt.unlabeled_caesar_context import extract,overlap_fragments,overlaps,letters


def test_numbered_prose_discards_navigation_and_keeps_raw_enclitics():
    raw=b'<p class="nav">[1] index</p><p>[1] 1 Viri armaque vident. 2 Iam?</p><p>[2] Atque venit!</p>'
    ss,meta=extract('test',raw)
    assert [[t['word'] for t in s['tokens']] for s in ss]==[['uiri','armaque','uident'],['iam'],['atque','uenit']]
    assert meta['chapters']==2


def test_overlap_ignores_spaces_enclitic_segmentation_and_orthography():
    sample=[dict(tokens=[dict(word=w) for w in ['uirorum','arma','que','uident']])]
    pieces=overlap_fragments(sample,width=12)
    assert overlaps(letters('VIRORUM armaque vident'),pieces,width=12)
    assert not overlaps(letters('diversa verba'),pieces,width=12)
