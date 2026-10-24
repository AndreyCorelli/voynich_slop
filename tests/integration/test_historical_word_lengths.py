import pytest
from benchmarks import historical_word_lengths as h


@pytest.mark.parametrize('text,german,expected',[
    ('Cæsar',False,'caesar'),('nichil',False,'nichil'),
    ('český',False,'cesky'),('czeſky',False,'czesky'),('ch',False,'ch'),
    ('uͤber',True,'uber'),('über',True,'uber'),('buͦch',True,'buoch'),
    ('größ',True,'gross'),('h`',True,'her'),("h'",True,'hus')])
def test_historical_letters_preserve_spelling_and_resolve_graphical_variants(text,german,expected):
    assert h.letters(text,german)==expected


def test_italian_apostrophe_boundary_sensitivity_is_explicit():
    assert list(h.lexical_tokens('dell’uomo'))==['delluomo']
    assert list(h.lexical_tokens('dell’uomo',apostrophe_split=True))==['dell','uomo']


def test_unresolved_abbreviation_is_a_barrier_in_complete_letter_analysis():
    assert list(h.lexical_tokens('a vn̅ b',german=True,exclude_unresolved=True))==['a',None,'b']
    assert list(h.lexical_tokens('a vn̅ b',german=True))==['a','vn','b']


def test_windows_do_not_bridge_excluded_words_or_independent_sources():
    words=['aaaa']*22
    result=h.distribution([words+[None]+words,words[:21]])
    assert result['windows']==2 and result['histogram_total_letters']=={88:2}
    assert result['nonoverlapping']['windows']==2


def test_exact_integer_ceiling_includes_104_and_excludes_105():
    equal=['aaaaa']*16+['aaaa']*6
    larger=['aaaaa']*17+['aaaa']*5
    result=h.distribution([equal,larger])
    assert result['windows_at_or_below_ceiling']==1
    assert result['fraction_at_or_below_ceiling']==.5
    assert result['median']==104.5/22


def test_czech_heading_inside_paragraph_does_not_discard_surrounding_prose(monkeypatch):
    html='''<div class="field--name-field-text-1">
      <p><strong>ÚVOD</strong></p>
      <p>Mnozy powyeſty <strong>Kap. 2</strong> hledagy mlu[f.001r]weno p&lt;ra&gt;wy.</p>
      <p><strong>Source:</strong> Modern publication details.</p></div>'''
    monkeypatch.setattr(h,'source',lambda _: (html.encode(),{'encoding':'utf-8'}))
    segments,_=h.czech_segments('diplomatic')
    words=[w for seg in segments for w in seg if w is not None]
    assert words==['mnozy','powyesty','hledagy','mluweno','prawy']
    assert any(w is None for seg in segments for w in seg)


def test_analysis_module_has_no_solver_dependency():
    from pathlib import Path
    import ast
    tree=ast.parse(Path(h.__file__).read_text())
    imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any(m and ('solver' in m or 'z3' in m) for m in imports)
