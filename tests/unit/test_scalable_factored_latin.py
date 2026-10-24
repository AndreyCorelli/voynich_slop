import json
from itertools import permutations, product
import numpy as np
import pytest
from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.scalable.latin_corpus import clean, balanced_order, sha, write
from voynich_smt.word_mapping.scalable.morphology_index import MorphologyIndex, alternatives
from voynich_smt.word_mapping.scalable.factored_lm import FactoredLatinModel, analysis_weights
from voynich_smt.word_mapping.scalable.latin_annotations import compatible
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram, BOS
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer, full_score
from voynich_smt.word_mapping.scalable.search import DictionarySearch, SearchConfig
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig, ContextIndex
from voynich_smt.word_mapping.scalable.trigram import load_model


def index_fixture(path, inventory, all_known=False):
    path.mkdir()
    arrays = {'offsets': np.array([0,1,2,4,5,6 if all_known else 5], dtype='uint64'),
              'lemma': np.array([0,0,1,2,2]+([1] if all_known else []), dtype='uint32'),
              'grammar': np.array([0,1,0,2,2]+([1] if all_known else []), dtype='uint32')}
    labels = {'lemma': {'l0':0,'l1':1,'l2':2}, 'grammar': {'g0':0,'g1':1,'g2':2}}
    files = {}
    for name, values in arrays.items():
        np.save(path/(name+'.npy'), values)
        files[name] = sha(path/(name+'.npy'))
    write(path/'labels.json', labels)
    write(path/'metadata.json', {'inventory_sha256':inventory.identity,'files':files,'labels_sha256':digest(labels)})
    return MorphologyIndex(path, inventory)


@pytest.fixture
def fitted(tmp_path):
    inventory = Inventory.build(tmp_path/'inventory.sqlite', ('a','b','c','d','e'))
    index = index_fixture(tmp_path/'morph', inventory)
    bigram = SparseBigram.train(inventory, ((0,1,2,0,1),(0,2,3,1,0)))
    weights, _ = analysis_weights(index, bigram.counts, supervised={2:2}, iterations=3)
    model = FactoredLatinModel(bigram, index, weights)
    yield inventory, model
    inventory.close()


def test_normalization_and_direct_marginalization(fitted):
    _, model = fitted
    for channel in model.channels:
        for u in range(BOS, model.size):
            assert sum(channel.probability(u,v) for v in range(model.size+1)) == pytest.approx(1., abs=1e-12)
            assert all(channel.probability(u,v)>0 for v in range(model.size+1))
    for u in range(BOS, model.size):
        assert sum(model.probability(u,v) for v in range(model.size+1)) == pytest.approx(1.)
    assert model.score((0,1,4)) == model.score_chunks(((0,),(1,4)))
    c = model.channels[0]
    for u,v in product(range(4),range(model.size+1)):
        expected = 0.
        for a,ra in c.members(u):
            for b,rb in c.members(v):
                t = (c.edges.get((a,b),0)+c.alpha*c.prior[b])/(c.totals[a]+c.alpha)
                e = (c.counts[v]+c.beta*c.base[v])*rb/c.mass[b]
                expected += ra*t*e
        assert c.probability(u,v) == pytest.approx((1-c.reserve)*expected+c.reserve*c.base[v])


def test_exact_moves_and_checkpoint(fitted, tmp_path):
    _, model = fitted
    stream = CipherStream(((0,1,0,2),(2,1)),3)
    for key in permutations(range(5),3):
        state = DictionaryState.create(stream,model,key)
        scorer = DictionaryScorer(model,stream,state)
        for cipher,word in product(range(3),range(5)):
            move = scorer.assign_or_swap(cipher,word)
            new = list(key)
            for row,value in move.changes:
                new[row] = value
            assert move.log_delta == pytest.approx(full_score(model,stream,DictionaryState.create(stream,model,new))-scorer.score,abs=1e-10)
    search = DictionarySearch(model,stream,seed=3,config=SearchConfig(proposals=15),
                  retrieval_config=RetrievalConfig(active_limit=4,total_entries=12,per_context=3))
    for _ in range(6):
        search.advance()
    path = tmp_path/'checkpoint.json'
    search.save(path)
    loaded = DictionarySearch.load(path,model,stream)
    for _ in range(9):
        assert search.advance() == loaded.advance()
    loaded.scorer.validate()


def test_serialization_and_surface_endpoint(fitted, tmp_path):
    inventory,model = fitted
    file = tmp_path/'model.sqlite'
    model.save(file)
    loaded = load_model(file,inventory)
    assert loaded.identity == model.identity
    assert loaded.score((0,1,2,4)) == model.score((0,1,2,4))
    loaded.mixture = (1,0,0)
    loaded._probability.cache_clear()
    assert loaded.score((0,1,2,4)) == model.bigram.score((0,1,2,4))
    assert not loaded.retrieval_is_exact
    assert ContextIndex(loaded,limit=3).query('successors',0)


def test_duplicate_analyses_and_crosswalk():
    entry = {'lemma_id':'l','part_of_speech':'N','enclitic':None,
             'inflections':[{'part_of_speech':'N','features':{'Case':'NOM','Number':'S','Gender':'C'}}]}
    assert alternatives([entry]) == alternatives([entry,entry])
    grammar = json.dumps(['N',[['Case','NOM'],['Number','S'],['Gender','C']],None])
    assert compatible(grammar,'NOUN',{'Case':'Nom','Number':'Sing','Gender':'Fem'})
    assert not compatible(grammar,'NOUN',{'Case':'Acc'})
    assert not compatible(grammar,'VERB',{})


def test_cleaner_and_author_balance():
    tokens,losses = clean('THE LATIN LIBRARY\nLIBER I\narma virumque cano et nunc ego de rebus multis loquor cum amicis meis.\n')
    assert 'library' not in tokens and 'arma' in tokens and losses
    rows = [{'id':'a','author':'a','tokens':100},{'id':'b','author':'b','tokens':10},
            {'id':'c','author':'b','tokens':10},{'id':'d','author':'a','tokens':100}]
    order = list(balanced_order(rows))
    assert len(order)==4 and order[0]['author']!=order[1]['author']
    assert order == list(balanced_order(list(reversed(rows))))


def test_all_known_inventory(tmp_path):
    inventory = Inventory.build(tmp_path/'inventory.sqlite', ('a','b','c','d','e'))
    try:
        index = index_fixture(tmp_path/'morph',inventory,all_known=True)
        base = SparseBigram.train(inventory,((0,1,2,3,4,0),))
        weights,_ = analysis_weights(index,base.counts)
        model = FactoredLatinModel(base,index,weights)
        assert all(sum(model.probability(u,v) for v in range(6))==pytest.approx(1.) for u in range(-1,5))
    finally:
        inventory.close()
