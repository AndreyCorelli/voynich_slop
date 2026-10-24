from collections import Counter
from dataclasses import asdict
import json

import pytest

from voynich_smt.data.acquisition import acquire, read_source
from voynich_smt.data.controls import control
from voynich_smt.data.corpus import Corpus, statistics
from voynich_smt.data.latin import LatinNormalization, normalize as latin
from voynich_smt.data.voynich import EvaNormalization, normalize as eva
from voynich_smt.models.text import Text

EVA = '''#=IVTFF Eva- 2.0 M 5
<f1r> <! $I=H $L=A>
<f1r.1,@P0> <%>ch.ar,or.[a:o]r.d?n.{ch}.@192;<$>
<f1r.2,+P0> a<->b<~>c<!remark>
<f1v> <! $I=S>
<f1v.1,@P0> <@I=T>ot.ol
<f1v.2,+P0> ar
'''
LATIN = '''Language: Latin
*** START OF THE PROJECT GUTENBERG EBOOK DEMO ***
English preface
C. IULI CAESARIS DE BELLO GALLICO COMMENTARIUS PRIMUS
GALLIA est omnis. Jūlius, vīvit; aqua! xxw.
C. IULI CAESARIS DE BELLO GALLICO COMMENTARIUS SECUNDUS
arma
*** END OF THE PROJECT GUTENBERG EBOOK DEMO ***
English license
'''


def test_eva_locations_annotations_and_exclusions():
    corpus = eva({'sha256': 'raw'}, EVA)
    assert corpus.records[0]['tokens'] == ['c', 'h']
    assert corpus.records[0]['folio'] == 'f1r'
    assert corpus.records[0]['section'] == 'H'
    assert corpus.records[0]['annotations'] == ['<%>', '<$>']
    assert sum(bool(r['excluded_reason']) for r in corpus.records) == 4
    assert [r['tokens'] for r in corpus.records if r['locus'] == 'f1r.2,+P0'] == [['a'], ['b'], ['c']]
    assert corpus.records[-1]['section'] == 'T'
    assert corpus.records[-1]['page_variables'].get('L') is None


def test_preserve_ambiguous_units_never_choose_reading():
    corpus = eva({}, EVA, EvaNormalization(annotated_words='preserve'))
    assert corpus.records[3]['tokens'] == ['[a:o]', 'r']
    assert corpus.records[4]['tokens'] == ['d', '?', 'n']
    assert corpus.records[5]['tokens'] == ['{ch}']
    assert corpus.records[6]['tokens'] == ['@192;']


@pytest.mark.parametrize('policy,expected', [('split', [('a',), ('b',)]), ('join', [('a', 'b')]), ('exclude-line', [])])
def test_uncertain_space_policy(policy, expected):
    c = eva({}, '#=IVTFF Eva- 2.0\n<f1r>\n<f1r.1,@P0> a,b', EvaNormalization(policy))
    assert [tuple(r['tokens']) for r in c.records if r['tokens']] == expected


def test_wrapped_locus_does_not_insert_space():
    c = eva({}, '#=IVTFF Eva- 2.0\n<f1r>\n<f1r.1,@P0> cho/\n/l.ar')
    assert [r['tokens'] for r in c.records] == [list('chol'), ['a', 'r']]
    with pytest.raises(ValueError):
        eva({}, '#=IVTFF Eva- 2.0\n<f1r.1,@P0> a/')


@pytest.mark.parametrize('text', ['#=IVTFF Cur- 2.0', '#=IVTFF Eva- 2.0\nbad'])
def test_wrong_eva_format_rejected(text):
    with pytest.raises(ValueError):
        eva({}, text)


def test_latin_boundaries_conventions_offsets_and_boilerplate():
    c = latin({}, LATIN)
    words = [''.join(r['tokens']) for r in c.records if r['tokens']]
    assert words == ['gallia', 'est', 'omnis', 'iulius', 'vivit', 'aqua', 'arma']
    assert any(r['excluded_reason'] == 'outside configured alphabet' for r in c.records)
    for r in c.records:
        assert LATIN[r['char_start']:r['char_end']] == r['raw']
    assert 'english' not in words and 'commentarius' not in words


@pytest.mark.parametrize('newline', ['\n', '\r\n'])
@pytest.mark.parametrize('preserve_spaces', [True, False])
def test_latin_prose_footer_before_formal_end_is_excluded(newline, preserve_spaces):
    raw = newline.join([
        '*** START OF THE PROJECT GUTENBERG EBOOK CAESAR ***',
        'GALLIA est omnis. XX.',
        "End of Project Gutenberg's Cæsar's Commentaries, Books I-IV, by Julius Cæsar",
        'other footer words',
        '*** END OF THE PROJECT GUTENBERG EBOOK CAESAR ***',
    ])
    corpus = latin({}, raw, LatinNormalization(preserve_spaces=preserve_spaces))
    tokens = [g for record in corpus.records for g in record['tokens']]
    assert ''.join(tokens) == 'galliaestomnisxx'
    assert corpus.normalization['parser_version'] == 2
    assert corpus.normalization['body_char_end'] == raw.index('End of Project Gutenberg')
    if preserve_spaces:
        for record in corpus.records:
            assert raw[record['char_start']:record['char_end']] == record['raw']
    else:
        assert corpus.records[0]['char_end'] == raw.index('End of Project Gutenberg')


@pytest.mark.parametrize('uv,expected', [('preserve','vivit'), ('v_to_u','uiuit'), ('u_to_v','vivit')])
def test_uv_explicit(uv, expected):
    c = latin({}, LATIN, LatinNormalization(uv=uv))
    assert expected in [''.join(r['tokens']) for r in c.records]


def test_latin_spaces_and_alphabet_policy():
    c = latin({}, LATIN, LatinNormalization(preserve_spaces=False))
    assert len(c.records) == 1
    assert ''.join(c.records[0]['tokens']) == 'galliaestomnisiuliusvivitaquaarma'
    c = latin({}, LATIN, LatinNormalization(j_to_i=False, alphabet='abcdefghijklmnopqrstuvwxyz'))
    assert 'julius' in [''.join(r['tokens']) for r in c.records]
    with pytest.raises(ValueError):
        latin({}, 'GALLIA est omnis')


@pytest.mark.parametrize('factory,kwargs', [(LatinNormalization, {'uv':'auto'}),
    (LatinNormalization, {'lowercase':1}), (LatinNormalization, {'alphabet':'aa'}),
    (EvaNormalization, {'uncertain_spaces':'auto'}), (EvaNormalization, {'tokenization':'glyphs'})])
def test_settings_validation(factory, kwargs):
    with pytest.raises(ValueError):
        factory(**kwargs)


def test_sample_exact_identity_filters_seed_and_budget(tmp_path):
    c = eva({'sha256':'abc'}, EVA)
    path = tmp_path / 'processed.json'
    c.save(path)
    loaded = Corpus.load(path)
    assert loaded.identity == c.identity
    text, metadata = loaded.sample(2, folio='f1v', section='T')
    assert text.words == (('o','t'), ('o','l'))
    assert metadata['record_indices'] == [10,11]
    assert loaded.sample(3, seed=7) == loaded.sample(3, seed=7)
    text, metadata = loaded.sample(3, max_tokens=3)
    assert text.words == (('c','h'),)
    assert metadata['selection']['whole_words_only']
    with pytest.raises(ValueError):
        loaded.sample(100)
    with pytest.raises(ValueError):
        loaded.sample(1, offset=1, seed=7)
    with pytest.raises(ValueError):
        loaded.sample(1, max_tokens=1)


def test_raw_import_immutable_and_checksum_verified(tmp_path):
    local = tmp_path / 'download.txt'
    local.write_text(EVA)
    source, decoded = acquire('zl-eva', tmp_path / 'raw', local=local)
    assert decoded == EVA
    manifest = tmp_path / 'raw/ZL3b-n.txt.manifest.json'
    assert read_source(manifest)[0] == source
    assert acquire('zl-eva', tmp_path / 'raw', local=local)[0] == source
    (tmp_path / 'raw/ZL3b-n.txt').write_text('tampered')
    with pytest.raises(ValueError, match='checksum'):
        read_source(manifest)


@pytest.mark.parametrize('kind', ['word-shuffle','within-word-shuffle','frequency-shuffle','uniform','prefix-stem-suffix'])
def test_controls_reproducible_and_matched(kind):
    text = Text.from_string('abba abc dddd')
    output, metadata = control(text, kind, 7)
    assert (output, metadata) == control(text, kind, 7)
    assert sorted(map(len, output.words)) == sorted(map(len, text.words))
    if kind in {'word-shuffle','within-word-shuffle','frequency-shuffle'}:
        assert Counter(g for w in output.words for g in w) == Counter(g for w in text.words for g in w)
    if kind == 'word-shuffle':
        assert Counter(output.words) == Counter(text.words)
    if kind == 'within-word-shuffle':
        assert all(Counter(a) == Counter(b) for a,b in zip(text.words,output.words))


def test_statistics_entropy_and_within_word_bigrams():
    s = statistics(Text.from_string('ab ab'))
    assert s['glyph_entropy_bits'] == 1
    assert s['within_word_conditional_entropy_bits'] == 0
    assert s['within_word_bigram_counts'] == [{'tokens':['a','b'], 'count':2}]
    assert statistics(Text(()))['tokens'] == 0
