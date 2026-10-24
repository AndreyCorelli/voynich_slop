import pytest
from benchmarks.frozen_key_holdout import next_block,decode_word,score
from voynich_smt.cipher.base import Encoder
from voynich_smt.models.text import Text
from voynich_smt.language.dictionary import WordDictionary


def test_decoder_roundtrip_and_partial_prefix_accounting():
    encoder=Encoder({'a':(('x',),),'b':(('y','z'),)})
    complete=decode_word(tuple('xyz'),encoder)
    assert complete['fully_decoded'] and complete['decoded_prefix']==['a','b']
    dead=decode_word(tuple('xyq'),encoder)
    assert not dead['fully_decoded'] and dead['complete_code_glyphs']==1 and dead['failure_index']==2
    incomplete=decode_word(tuple('xy'),encoder)
    assert incomplete['complete_code_glyphs']==1 and incomplete['failure']=='incomplete final code'


def test_dictionary_membership_requires_complete_decoding_and_novelty_is_explicit():
    encoder=Encoder({'a':(('x',),),'b':(('y','z'),)})
    result=score(Text.from_string('x xy xyz'),encoder,WordDictionary.from_strings(('a','ab')),
                 (tuple('x'),))
    assert result['fully_decoded_words']==result['dictionary_words']==2
    assert result['seen_ciphertext_words']==1
    assert result['novel_dictionary_words']==1
    assert not result['word_results'][1]['dictionary_member']


def test_immediate_holdout_cannot_skip_exclusions_or_cross_folio():
    records=[{'tokens':list(w),'folio':'f1'} for w in ('a','b','c','d')]
    text,meta=next_block(records,Text.from_string('a b'),size=2)
    assert text==Text.from_string('c d') and meta['holdout_record_indices']==[2,3]
    records[2]['tokens']=[]
    with pytest.raises(ValueError,match='excluded'):next_block(records,Text.from_string('a b'),size=2)
    records[2]['tokens']=list('c');records[3]['folio']='f2'
    with pytest.raises(ValueError,match='folio'):next_block(records,Text.from_string('a b'),size=2)


def test_training_match_must_be_unique():
    records=[{'tokens':['a'],'folio':'f1'}]*4
    with pytest.raises(ValueError,match='one exact'):next_block(records,Text.from_string('a'),size=2)
