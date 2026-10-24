import json
import numpy as np

from benchmarks.scalable_english_run import run
from voynich_smt.word_mapping.scalable.classes import ClassWordModel
from voynich_smt.word_mapping.scalable.confidence import extract,truth_labels,fit,predict,evaluate
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.search import SearchConfig
from voynich_smt.data.corpus import digest


def test_class_word_and_confidence_public_only_pipeline(tmp_path):
    resources=tmp_path/'resources';resources.mkdir()
    inventory=Inventory.build(resources/'inventory.sqlite',('a','et','in','non','sed','ut'))
    docs=((0,1,0,2,1,3),(3,2,1,0,2),(0,3,1,2))
    try:
        base=SparseBigram.train(inventory,docs,config=ModelConfig(language='la',tokenization='latin-iu-continuous-v1'))
        model=ClassWordModel.train(base,docs,k=2,contexts=3,dimensions=2,iterations=4)
        model.save(resources/'model.sqlite')
    finally:inventory.close()
    public,truth=generate((('et','in','a','et','non','in','et','a'),),seed=83,tokenization='latin-iu-continuous-v1')
    fixture=tmp_path/'fixture';public.save(fixture/'public/cipher.json');truth.save(tmp_path/'private.json')
    output=tmp_path/'run'
    run(resources,fixture/'public/cipher.json',output,seeds=(3,5,7),
        config=SearchConfig(initialization='frequency',proposals=30),trace=True)
    # Neither inference nor feature extraction receives any truth path.
    features=extract(resources,output)
    assert features['rows'] and all('original' not in r and 'correct' not in r for r in features['rows'])
    assert len({r['word_id'] for r in features['rows']})==len(features['rows'])
    inventory=Inventory(resources/'inventory.sqlite')
    try:labels=truth_labels(features,json.loads((tmp_path/'private.json').read_text()),inventory)
    finally:inventory.close()
    frozen=fit(features,labels);before=digest(frozen)
    probabilities=predict(frozen,features);report=evaluate(features,labels,probabilities)
    assert np.isfinite(probabilities).all() and digest(frozen)==before
    assert report['candidate_types']==len(labels)
    assert report['top']['50']['types']==len(labels)
