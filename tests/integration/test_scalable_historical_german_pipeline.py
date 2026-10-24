import json
from benchmarks.scalable_english_run import run
from benchmarks.scalable_english_evaluate import evaluate
from voynich_smt.word_mapping.scalable.historical_german import parse_cora,TOKENIZATION
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.search import SearchConfig
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig


def test_unicode_historical_surface_public_only_search_and_rescoring(tmp_path):
    document=parse_cora('''<text id="F"><cora-header/><token id="t1"><tok_anno utf="Der"/></token>
    <token id="t2"><tok_anno utf="buͦch"/></token><token id="t3"><tok_anno utf="vn̄d"/></token>
    <token id="t4"><tok_anno utf="ſein"/></token></text>''')
    words=document.segments[0];resources=tmp_path/'resources';resources.mkdir()
    inventory=Inventory.build(resources/'inventory.sqlite',(*words,'ärger'),tokenization=TOKENIZATION)
    try:
        model=SparseBigram.train(inventory,[[inventory.id(w) for w in words]*3],config=ModelConfig(language='de',tokenization=TOKENIZATION))
        model.save(resources/'model.sqlite')
        (resources/'report.json').write_text(json.dumps({'limitations':['Toy historical German fixture.']}))
        stream,truth=generate((words,),seed=83,tokenization=TOKENIZATION);public=tmp_path/'public/cipher.json';stream.save(public)
        output=tmp_path/'run'
        inferred=run(resources,public,output,seeds=(3,5,7),config=SearchConfig(proposals=20),retrieval=RetrievalConfig(active_limit=5,total_entries=20,per_context=3),trace=True)
        assert all(r['step']==20 for r in inferred['runs'])
        # Truth does not even exist on disk until search has finished.
        private=tmp_path/'evaluation-only/truth.json';truth.save(private)
        metrics=evaluate(resources,output,private)
        assert metrics['tokens']==4 and len(metrics['runs'])==3
        assert not any('EWT' in s or 'Older literary English' in s for s in metrics['limitations'])
        assert metrics['grammar']=='not_evaluated'
    finally:inventory.close()


def test_dta_original_reading_survives_fixture_generation(tmp_path):
    from voynich_smt.word_mapping.scalable.historical_german_tei import parse_dta
    data='''<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/><text><body>
    <p><hi>D</hi>As <choice><sic>Chriſtns</sic><corr>Christus</corr></choice> Men-<lb/>
    <fw>ſchen</fw><pb/><fw>Header</fw><lb/>ſchen vñ buͤch.</p>
    </body></text></TEI>'''
    doc=parse_dta(data);stream,truth=generate(doc.segments,seed=83,tokenization=TOKENIZATION)
    assert truth.plaintext==(('das','christns','menschen','vñ','buͤch'),)
    assert 'christus' not in truth.decoding
    path=tmp_path/'cipher.json';stream.save(path)
    public=json.loads(path.read_text())
    assert public['tokenization']==TOKENIZATION
    assert all(type(c) is int for d in public['documents'] for c in d)
