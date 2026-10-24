from dataclasses import replace
from itertools import permutations,product
from collections import Counter
import json
import math

import numpy as np
import pytest

from voynich_smt.word_mapping.scalable.classes import ClassWordModel
from voynich_smt.word_mapping.scalable.class_decode import ClassDecoder,initialize_classes
from voynich_smt.word_mapping.scalable.confidence import FEATURES,fit,predict,evaluate,wilson
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram,BOS
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer,full_score
from voynich_smt.word_mapping.scalable.retrieval import ContextIndex,RetrievalConfig
from voynich_smt.word_mapping.scalable.search import DictionarySearch,SearchConfig
from voynich_smt.word_mapping.scalable.trigram import load_model


@pytest.fixture
def resources(tmp_path):
    inventory=Inventory.build(tmp_path/'inventory.sqlite',('a','b','c','d','e','f'))
    docs=((0,1,0,2,0),(3,2,1,0),(2,1,3,0))
    bigram=SparseBigram.train(inventory,docs)
    model=ClassWordModel.train(bigram,docs,k=2,contexts=3,dimensions=2,iterations=6,seed=23)
    yield inventory,model,CipherStream(((0,1,0,2),(2,1)),3)
    inventory.close()


def test_class_word_normalized_full_support_and_serialization(resources,tmp_path):
    inventory,model,_=resources
    for a in range(BOS,model.size):
        assert sum(model.probability(a,b) for b in range(model.size+1))==pytest.approx(1.)
        assert all(model.probability(a,b)>0 for b in range(model.size+1))
    for b in range(model.size+1):assert model.base_probability(b)==model.bigram.base_probability(b)
    path=tmp_path/'model.sqlite';model.save(path);loaded=load_model(path,inventory)
    assert loaded.identity==model.identity and list(loaded.labels)==list(model.labels)
    assert loaded.score((0,1,4,2))==model.score((0,1,4,2))
    assert model.score_chunks(((0,1),(4,2)))==model.score((0,1,4,2))
    for key in permutations(range(model.size),3):
        state=DictionaryState.create(resources[2],model,key);scorer=DictionaryScorer(model,resources[2],state)
        for c,w in product(range(3),range(model.size)):
            move=scorer.assign_or_swap(c,w);new=list(key)
            for row,word in move.changes:new[row]=word
            assert move.log_delta==pytest.approx(full_score(model,resources[2],DictionaryState.create(resources[2],model,new))-scorer.score,abs=1e-9)


def test_class_retrieval_is_exact_beyond_observed_word_edges(tmp_path):
    forms=['w'+chr(97+i//26)+chr(97+i%26) for i in range(40)]
    inventory=Inventory.build(tmp_path/'inventory.sqlite',forms)
    try:
        docs=((0,1,0,2),(2,1,0))
        base=SparseBigram.train(inventory,docs);model=ClassWordModel.train(base,docs,k=2,contexts=2,dimensions=2,iterations=3)
        index=ContextIndex(model,limit=20)
        for left in (BOS,0,1,30):
            expected=tuple(sorted(range(model.size),key=lambda w:(-model.probability(left,w),w))[:20])
            assert index.query('successors',left)==expected
        for right in (0,1,30,model.eos):
            expected=tuple(sorted(range(model.size),key=lambda w:(-model.probability(w,right),w))[:20])
            assert index.query('predecessors',right)==expected
    finally:inventory.close()


def test_class_channel_deltas_capacity_lifting_and_checkpoint(resources,tmp_path):
    _,model,stream=resources
    for key in product(range(model.nclasses),repeat=3):
        try:decoder=ClassDecoder(model,stream,key)
        except ValueError:continue
        assert decoder.score==pytest.approx(decoder.full_score())
        for cipher,cluster in product(range(3),range(model.nclasses)):
            changes={cipher:cluster};new=list(key);new[cipher]=cluster
            try:move=decoder.proposal(changes)
            except ValueError:continue
            expected=ClassDecoder(model,stream,new).full_score()-decoder.full_score()
            assert move[0]==pytest.approx(expected,abs=1e-9)
    state=initialize_classes(stream,model,seed=3,steps=30)
    assert state==initialize_classes(stream,model,seed=3,steps=30)
    assert len(set(state.assignments))==3
    search=DictionarySearch(model,stream,seed=3,config=SearchConfig(initialization='classes',proposals=30),
                            retrieval_config=RetrievalConfig(active_limit=4,total_entries=12))
    for _ in range(11):search.advance()
    path=tmp_path/'checkpoint.json';search.save(path);resumed=DictionarySearch.load(path,model,stream)
    for _ in range(19):assert search.advance()==resumed.advance()
    assert search.joint_archive==resumed.joint_archive
    resumed.scorer.validate()


def test_class_model_with_no_untrained_inventory(tmp_path):
    inventory=Inventory.build(tmp_path/'inventory.sqlite',('a','b','c'))
    try:
        docs=((0,1,2,0,1,0),)
        base=SparseBigram.train(inventory,docs);model=ClassWordModel.train(base,docs,k=2,contexts=2,dimensions=2,iterations=3)
        assert all(sum(model.probability(a,b) for b in range(model.size+1))==pytest.approx(1) for a in range(BOS,model.size))
    finally:inventory.close()


def test_confidence_fit_is_method_bound_and_not_word_identity_bound():
    rng=np.random.default_rng(23);x=rng.normal(size=(200,len(FEATURES)))
    labels=(x[:,0]+x[:,1]>.7).astype(float)
    public={'signature':{'model':'source-only','runs':3},'total_tokens':200,'rows':[
        {'cipher':i,'word_id':i,'votes':3,'count':1,'features':features.tolist()} for i,features in enumerate(x)]}
    frozen=fit(public,labels);saved=json.loads(json.dumps(frozen))
    p=predict(saved,public);assert np.mean((p-labels)**2)<.1
    renamed=json.loads(json.dumps(public))
    for r in renamed['rows']:r['word_id']+=10000
    assert np.array_equal(p,predict(saved,renamed))
    report=evaluate(public,labels,p);assert report['top']['10']['types']==10
    assert frozen['training_types']==200 and frozen['positive_types']==int(labels.sum())
    changed=json.loads(json.dumps(public));changed['signature']['model']='different'
    with pytest.raises(ValueError,match='signature'):predict(saved,changed)
    assert wilson(0,0)==[None,None] and wilson(20,20)[0]>.8 and wilson(1,1)[0]<.8
    assert np.max(predict(fit(public,np.zeros(200)),public))<.001
