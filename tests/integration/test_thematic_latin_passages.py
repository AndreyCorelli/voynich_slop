from benchmarks.thematic_latin_passages import tokens,extract


def test_unknown_editorial_material_and_diagram_labels_are_barriers():
    out=tokens('terra [et situm] luna /11/ sol * aqua A B C',diagrams=True)
    assert out==['terra',None,'luna',None,'sol',None,'aqua',None,None,None]
    assert tokens('uero jupiter')==['uero','jupiter']


def test_sphaera_start_chapter_boundaries_and_inline_words():
    html=b'''<div class="mw-parser-output"><p>Foreign header</p>
    <p>[Cap. 1.]</p><p>/11/ Intentio nostra in <i>hoc</i> tractatu</p>
    <p>[Cap. 2.]</p><p>luna [unknown] semidiametrorum</p></div>'''
    segments,audit=extract('sphaera',html)
    assert segments==[['intentio','nostra','in','hoc','tractatu'],['luna',None,'semidiametrorum']]
    assert audit['chapter_breaks_after_incipit']==1


def test_manilius_incipt_gap_footer_and_numbers_preserved_as_barriers():
    html=b'''<p>BOOK HEADER</p><p>Carmine divinas <i>artes</i> [22] et 5 sol</p>
    <p>* * *</p><p>luna uero</p><p>Manilius The Miscellany The Latin Library</p>'''
    segments,_=extract('manilius1',html)
    assert segments==[['carmine','divinas','artes',None,'et',None,'sol'],['luna','uero']]


def test_emerald_statements_remain_separate():
    html='<div class="mw-parser-output"><div class="text"><ol>'
    texts=['VERUM SINE MENDACIO']+['EST SOL']*13+['COMPLETUM EST']
    html+=''.join('<li>'+t+'</li>' for t in texts)+'</ol></div></div>'
    segments,audit=extract('emerald',html.encode())
    assert len(segments)==audit['statement_boundaries']==15
    assert segments[0]==['verum','sine','mendacio']
