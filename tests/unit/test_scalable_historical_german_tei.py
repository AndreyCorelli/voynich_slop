import pytest
from voynich_smt.word_mapping.scalable.historical_german_tei import parse_dta


def wrap(text):
    return '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/><text><body>'+text+'</body></text></TEI>'


def test_original_choices_inline_initials_and_physical_line_wraps():
    doc=parse_dta(wrap('<p><hi>D</hi>As buͤch <choice><sic>Chriſtns</sic><corr>Christus</corr></choice> vñ '+
        '<choice><abbr>d̕</abbr><expan>der</expan></choice> Men-<lb/>'+ 
        '<fw type="catch">ſchen</fw><pb/><fw>Header</fw><lb/>ſchen '+
        '<choice><orig>ver<lb/>ſpottet</orig><reg>ver-<lb/>ſpottet</reg></choice>.</p>'))
    assert doc.segments==(('das','buͤch','christns','vñ','d̕','menschen','verspottet'),)
    assert doc.statistics['choice_sic']==1 and doc.statistics['joined_line_hyphens']==1


def test_marginalia_do_not_split_words_and_gaps_remove_partial_fragments():
    doc=parse_dta(wrap('<p>ge<note>comment</note>ſagt ver<gap reason="illegible"/>rt ſich.</p><p>gut!</p>'))
    assert doc.segments==(('gesagt',),('sich','gut'))
    assert doc.statistics['gaps']==1
    assert 'comment' not in sum(doc.segments,())


def test_no_implicit_modernization_or_unsupported_choice():
    with pytest.raises(ValueError,match='Unsupported TEI choice'):
        parse_dta(wrap('<choice><reg>modern</reg></choice>'))
