from pathlib import Path
import json
from benchmarks.scalable_english_run import run
from benchmarks.scalable_english_evaluate import evaluate
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.shuffle_contrast import ShuffleContrast
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.search import SearchConfig
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig


def test_public_only_contrast_search_and_score_validation(tmp_path):
    resources=tmp_path/'resources';resources.mkdir()
    inventory=Inventory.build(resources/'inventory.sqlite',tuple('abcdefgh'))
    try:
        docs=((0,1,0,2,0,1,3,0,2,1,0),)
        base=SparseBigram.train(inventory,docs,config=ModelConfig(language='la',tokenization='latin-iu-continuous-v1'))
        model=ShuffleContrast(base,shuffles=3);model.save(resources/'model.sqlite')
        stream,truth=generate((tuple('abacabdacba'),),seed=83,tokenization='latin-iu-continuous-v1')
        public=tmp_path/'public/cipher.json';stream.save(public)
        output=tmp_path/'run'
        result=run(resources,public,output,seeds=(3,5,7),config=SearchConfig(proposals=25),
               retrieval=RetrievalConfig(active_limit=5,total_entries=20,per_context=3),trace=True)
        assert len(result['runs'])==3 and all(r['step']==25 for r in result['runs'])
        assert 'not likelihood' in result['protocol']['scope']
        # Truth is created only after all real inference has finished.
        private=tmp_path/'evaluation-only/truth.json';truth.save(private)
        evaluation=evaluate(resources,output,private)
        assert len(evaluation['runs'])==3
        assert not (output/'evaluation-only').exists()
    finally:inventory.close()


def test_parallel_trial_fixtures_do_not_share_private_directory(tmp_path,monkeypatch):
    from benchmarks import scalable_latin_shuffle_contrast as experiment
    source=tmp_path/'fixture'
    (source/'public').mkdir(parents=True)
    (source/'evaluation-only').mkdir()
    (source/'public/cipher.json').write_text('{}')
    (source/'evaluation-only/truth.json').write_text('{}')
    monkeypatch.setattr(experiment,'ROOT',tmp_path/'experiment')
    a=experiment.isolated_fixture(source,'a')
    (a/'evaluation-only').rename(a/'hidden')
    b=experiment.isolated_fixture(source,'b')
    assert (b/'evaluation-only/truth.json').exists()
    assert (source/'evaluation-only/truth.json').exists()
    assert not (a/'evaluation-only').exists()
