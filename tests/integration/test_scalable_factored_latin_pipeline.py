from pathlib import Path

from benchmarks.scalable_english_run import run
from voynich_smt.word_mapping.scalable.latin_corpus import census, documents, clean
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.morphology_index import MorphologyIndex
from voynich_smt.word_mapping.scalable.factored_lm import FactoredLatinModel, analysis_weights
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.search import SearchConfig
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig


def test_public_only_morphology_decoder(tmp_path):
    resources = tmp_path/'resources'
    resources.mkdir()
    inventory = Inventory.build(resources/'inventory.sqlite', ('et','in','puella','puellam','puellae','uenit','uenire','amat','amare','nouum'))
    try:
        index = MorphologyIndex.build(tmp_path/'morphology',inventory,Path('data/vendor/whitakers-words'),batch=3)
        assert index.analyses(inventory.id('puella'))
        docs = [tuple(map(inventory.id, words)) for words in [('puella','uenit','et','puella','amat'),('puellam','amat','et','uenit')]]
        base = SparseBigram.train(inventory,docs,config=ModelConfig(language='la',tokenization='latin-iu-continuous-v1'))
        weights,_ = analysis_weights(index,base.counts)
        model = FactoredLatinModel(base,index,weights)
        model.save(resources/'model.sqlite')
        stream,truth = generate((('puella','uenit','et','puella','amat'),),seed=83,tokenization='latin-iu-continuous-v1')
        public = tmp_path/'public/cipher.json'
        stream.save(public)
        # There is no truth artifact or held-out plaintext input to inference.
        output = tmp_path/'inference'
        result = run(resources,public,output,seeds=(3,5,7),config=SearchConfig(proposals=12),
                     retrieval=RetrievalConfig(active_limit=5,total_entries=30,per_context=4))
        assert len(result['runs'])==3
        for r in result['runs']:
            assert r['step']==12
            assert len(set(r['joint_archive'][0]['assignments']))==stream.type_count
        assert not (output/'evaluation-only').exists()
    finally:
        inventory.close()


def test_corpus_quarantine_duplicates_and_frozen_split(tmp_path):
    source = tmp_path/'raw'
    (source/'known').mkdir(parents=True)
    (source/'unregistered').mkdir()
    # Synthetic distinct tokens keep accidental overlap independent of Latin.
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    text = ' '.join('w'+a+b for a in alphabet for b in alphabet)
    (source/'known/a.txt').write_text(text)
    (source/'known/duplicate.txt').write_text(text)
    (source/'unregistered/x.txt').write_text(text)
    # Prepare a >=1000-token heldout whose shingles are distinct.
    hold = ' '.join('z'+a+b for a in alphabet for b in alphabet)*3
    (source/'heldout.txt').write_text(hold)
    design = {'source':{'id':'test'},'excluded_authors':['reserved'],
              'training_directories':{'known':'training'},'heldouts':[{'id':'reserved','path':'heldout.txt','author':'reserved','split':'sealed-test'}],
              'maximum_target_tokens':35000,'minimum_document_tokens':100,
              'training_sizes':[100,1000],'excluded_filename_fragments':['index']}
    out = tmp_path/'corpus'
    report = census(source,out,design)
    assert len(report['documents'])==1
    assert report['duplicates'][0]['kind']=='exact'
    assert report['subsets']['100']['documents']==report['subsets']['1000']['documents']
    assert any(r['reason']=='unregistered_source' for r in report['rejected'])
    assert len(list(documents(out,report['documents'])))==1


def test_source_navigation_cleaning():
    prose = 'arma uirumque cano et nunc ego de rebus multis loquor cum amicis meis.'
    text = 'M. TVLLI CICERONIS EPISTVLARVM AD FAMILIARES LIBER SEXTVS Ad A. Torquatum et Ceteros\n I II III IV V VI VII VIII IX Xa Xb XI XII XIII XIV\nCAPUT 3 1 '+prose
    tokens,losses = clean(text)
    assert 'caput' not in tokens and 'torquatum' not in tokens and 'xiii' not in tokens
    assert tokens[0]=='arma'
    assert losses['heading']>0
