import json
import pytest
from voynich_smt.word_mapping.scalable.historical_german import parse_cora,normalize_surface,TOKENIZATION
from voynich_smt.word_mapping.scalable.data import generate,CipherStream
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram


def test_historical_spelling_and_annotation_isolation():
    source='''<text id="F001"><cora-header/><header>text-author: Example</header>
    <token id="t1"><tok_dipl utf="WRONG"/><tok_anno utf="Buͦch"><lemma tag="buch"/></tok_anno><tok_anno utf="/"/></token>
    <token id="t2"><tok_anno utf="Vn̄d"/></token><token id="t3"><tok_anno utf="ſein"/></token></text>'''
    doc=parse_cora(source)
    assert doc.segments==(('buͦch','vn̄d','sein'),)
    assert doc.annotations[0]['lemma']=='buch'
    assert normalize_surface('Ärger')=='ärger'
    assert normalize_surface('bu\u200doch')=='buoch'
    assert normalize_surface('jünger')=='jünger'


def test_gaps_and_missing_text_never_join_but_sentences_do():
    doc=parse_cora('''<text id="F"><cora-header/>
    <token id="t1"><tok_anno utf="der"/><tok_anno utf="."/></token>
    <token id="t2"><tok_anno utf="mann"/></token><token id="t3"><tok_anno utf="[unlesbar]"/></token>
    <token id="t4"><tok_anno utf="ist"/></token><token id="t5"/>
    <token id="t6"><tok_anno utf="hie"/></token></text>''')
    assert doc.segments==( ('der','mann'),('ist',),('hie',))


def test_noncontiguous_pages_are_barriers_not_line_boundaries():
    doc=parse_cora('''<text id="F"><cora-header/><layoutinfo>
    <page no="1" range="c1"/><column id="c1" range="l1"/><line id="l1" range="t1_d1"/>
    <page no="2" range="c2"/><column id="c2" range="l2"/><line id="l2" range="t2_d1"/>
    <page no="10" range="c3"/><column id="c3" range="l3"/><line id="l3" range="t3_d1"/>
    </layoutinfo><token id="t1"><tok_anno utf="der"/></token><token id="t2"><tok_anno utf="mann"/></token>
    <token id="t3"><tok_anno utf="ist"/></token></text>''')
    assert doc.segments==(('der','mann'),('ist',))


def test_unicode_resource_and_cipher_roundtrip_preserves_legacy_contract(tmp_path):
    words=('buͦch','vn̄d','ärger','sein')
    with pytest.raises(ValueError):Inventory.build(tmp_path/'bad.sqlite',words)
    inventory=Inventory.build(tmp_path/'inventory.sqlite',words,tokenization=TOKENIZATION)
    try:
        model=SparseBigram.train(inventory,[[inventory.id(w) for w in words]],config=ModelConfig(language='de',tokenization=TOKENIZATION))
        model.save(tmp_path/'model.sqlite')
        assert SparseBigram.load(tmp_path/'model.sqlite',inventory).identity==model.identity
        stream,truth=generate((words,),seed=83,tokenization=TOKENIZATION);stream.save(tmp_path/'cipher.json')
        assert CipherStream.load(tmp_path/'cipher.json')==stream
        assert tuple(truth.decoding[c] for c in stream.documents[0])==words
        assert set(json.loads((tmp_path/'cipher.json').read_text()))=={'documents','type_count','format_version','tokenization','sha256'}
    finally:inventory.close()
