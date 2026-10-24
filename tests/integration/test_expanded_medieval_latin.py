import pytest
from benchmarks.expanded_medieval_latin import extract_html, Paragraphs, load_work, WORKS


def footer():
    return '<p><a href="/medieval.html">Medieval Latin</a></p>'


def test_malformed_unclosed_paragraphs_do_not_truncate_or_duplicate_body():
    raw=('<p>UNIVERSIS Christi fidelibus<p>Capitulum I<p>Title<p>prima verba'
         '<p>Capitulum II<p>Second title<p>ultima verba'+footer()).encode()
    words,audit=extract_html(raw,'utf-8','bury','UNIVERSIS Christi fidelibus')
    assert [w for w in words if w] == ['universis','christi','fidelibus','prima','verba','ultima','verba']
    assert words.count(None)==4


def test_inline_markup_does_not_split_one_word():
    raw=('<p>Vitam et conversa<b>tionem</b><p>[1] nova verba'+footer()).encode()
    words,audit=extract_html(raw,'utf-8','einhard','Vitam et conversationem')
    assert words==['vitam','et','conversationem',None,'nova','verba']


def test_dante_edition_numbers_are_removed_but_chapter_boundaries_remain():
    raw=('<p class="pagehead">Title</p><p><b>I.</b>1. Prima verba. 2. Alia verba.'
         '<p><b>II.</b>1. Ultima verba.'+footer()).encode()
    words,audit=extract_html(raw,'utf-8','dante')
    assert [w for w in words if w]==['prima','verba','alia','verba','ultima','verba']
    assert words.count(None)==2


def test_notes_break_runs_and_explicit_book_tail_is_excluded():
    raw=('<p>[i] prima [editorial note] ultima<p>Explicit liber I. Incipit secundus.'+footer()).encode()
    words,audit=extract_html(raw,'utf-8','gesta')
    assert words==[None,'prima',None,'ultima',None]


def test_wrong_encoding_is_handled_strictly_and_recorded():
    raw=('<p>[i] prima\xa0ultima'+footer()).encode('windows-1252')
    words,audit=extract_html(raw,'utf-8','gesta')
    assert words==[None,'prima','ultima']
    assert audit['encoding_used']=='windows-1252'


@pytest.mark.parametrize('raw',[b'<p>Not the expected start</p>',b'<p>[i] no footer</p>'])
def test_missing_body_or_footer_fails_closed(raw):
    with pytest.raises(ValueError,match='anchor'):
        extract_html(raw,'utf-8','gesta')


def test_complete_bury_reaches_last_chapters_and_gesta_books_stay_separate():
    work=next(w for w in WORKS if w['id']=='bury')
    segments,metadata,audit=load_work(work)
    words=[w for w in segments[0] if w]
    assert len(words)>14000
    # Last chapter's first sentence must survive the malformed chapter-VII markup.
    joined=' '.join(words)
    assert 'tempus jam efflagitat terminare tractatum' in joined
    gesta=next(w for w in WORKS if w['id']=='gesta')
    segments,metadata,audit=load_work(gesta)
    assert len(segments)==len(metadata)==len(audit)==10
