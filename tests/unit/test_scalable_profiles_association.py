from collections import Counter
from itertools import permutations, product

import pytest

from voynich_smt.word_mapping.scalable.association import AssociationModel, pair_counts
from voynich_smt.word_mapping.scalable.profiles import raw_profiles, percentile_profiles
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer, EventIndex, full_score
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.search import DictionarySearch, SearchConfig
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
from voynich_smt.word_mapping.scalable.trigram import load_model


@pytest.fixture
def resources(tmp_path):
    inventory=Inventory.build(tmp_path/'inventory.sqlite',('a','b','c','d','e'))
    docs=((0,1,0,2,0,3),(2,1,2,1),(3,0,2))
    bigram=SparseBigram.train(inventory,docs)
    pairs=Counter()
    for doc in docs:pairs.update(pair_counts(doc,(1,2,4)))
    model=AssociationModel(bigram,pairs)
    stream=CipherStream(((0,1,2,0,1),(2,1),(0,)),3)
    yield inventory,model,stream
    inventory.close()


def test_profiles_are_label_invariant_and_initialization_is_complete(resources):
    _,model,stream=resources
    counts=Counter({0:10,1:5,2:2});edges=Counter({(0,1):4,(1,0):3,(0,2):2,(2,0):1})
    original=raw_profiles(counts,edges); rename={0:17,1:5,2:31}
    renamed=raw_profiles({rename[w]:n for w,n in counts.items()},
                         {(rename[a],rename[b]):n for (a,b),n in edges.items()})
    assert all(original[w]==renamed[rename[w]] for w in original)
    ids,values=percentile_profiles(original)
    assert values.shape==(3,9) and values.min()>=0 and values.max()<=1
    first=DictionaryState.initialize(stream,model,method='profile',seed=3)
    assert first==DictionaryState.initialize(stream,model,method='profile',seed=3)
    assert len(set(first.assignments))==stream.type_count
    # Initialization depends on counts/edges only, not the scoring objective.
    assert first==DictionaryState.initialize(stream,model.bigram,method='profile',seed=3)


def test_association_exact_moves_multi_document_chunking_and_serialization(resources,tmp_path):
    inventory,model,stream=resources
    assert pair_counts((0,1,2,0),(1,2))==Counter({(0,1):1,(1,2):1,(2,0):1,(0,2):1,(1,0):1})
    for key in permutations(range(model.size),3):
        state=DictionaryState.create(stream,model,key);scorer=DictionaryScorer(model,stream,state)
        assert scorer.score==pytest.approx(full_score(model,stream,state),abs=1e-10)
        for cipher,word in product(range(3),range(model.size)):
            move=scorer.assign_or_swap(cipher,word);new=list(key)
            for c,w in move.changes:new[c]=w
            assert move.log_delta==pytest.approx(full_score(model,stream,DictionaryState.create(stream,model,new))-scorer.score,abs=1e-10)
        move=scorer.propose({0:key[1],1:key[2],2:key[0]});scorer.commit(move);scorer.validate()
    assert model.score_chunks(((0,1),(2,0)))==model.score((0,1,2,0))
    assert model.score((0,))==0
    path=tmp_path/'model.sqlite';model.save(path);loaded=load_model(path,inventory)
    assert loaded.identity==model.identity and loaded.score((0,1,2,0))==model.score((0,1,2,0))
    with pytest.raises(ValueError,match='Event index'):
        DictionaryScorer(model,stream,state,event_index=EventIndex.build(stream))
    other=AssociationModel(model.bigram,model.pairs,distances=(1,))
    with pytest.raises(ValueError,match='Event index'):
        DictionaryScorer(other,stream,state,event_index=scorer.index)
    with pytest.raises(ValueError): AssociationModel(model.bigram,model.pairs,distances=(2,1))
    with pytest.raises(ValueError): AssociationModel(model.bigram,{(4,0):1})


@pytest.mark.parametrize('objective',['bigram','association'])
def test_profile_and_association_checkpoint_continuation(resources,tmp_path,objective):
    _,model,stream=resources
    if objective=='bigram':model=model.bigram
    search=DictionarySearch(model,stream,seed=3,config=SearchConfig(initialization='profile',proposals=60),
                            retrieval_config=RetrievalConfig(active_limit=4,total_entries=12,per_context=3))
    for _ in range(21):search.advance()
    path=tmp_path/'checkpoint.json';search.save(path)
    resumed=DictionarySearch.load(path,model,stream)
    for _ in range(39):assert search.advance()==resumed.advance()
    assert search.joint_archive==resumed.joint_archive
    search.scorer.validate();resumed.scorer.validate()


def test_association_has_zero_discrepancy_for_its_own_graph(resources):
    inventory,_,_=resources
    document=(0,1,0,1,0,2,3,0,1,0,2)
    bigram=SparseBigram.train(inventory,(document,))
    model=AssociationModel(bigram,pair_counts(document,(1,2,4)))
    assert model.score(document)==pytest.approx(0.,abs=1e-12)
    wrong=tuple({0:1,1:0,2:2,3:3}[w] for w in document)
    assert model.score(wrong)<0
