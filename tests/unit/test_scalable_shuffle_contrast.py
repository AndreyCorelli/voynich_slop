from collections import Counter
from itertools import permutations as keys, product
import math
import pytest

from voynich_smt.word_mapping.scalable.shuffle_contrast import ShuffleContrast,signed_pairs,permutations
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer,full_score
from voynich_smt.word_mapping.scalable.search import DictionarySearch,SearchConfig
from voynich_smt.word_mapping.scalable.retrieval import ContextIndex,RetrievalConfig
from voynich_smt.word_mapping.scalable.trigram import load_model


@pytest.fixture
def model(tmp_path):
    inv=Inventory.build(tmp_path/'inventory.sqlite',tuple('abcdefgh'))
    base=SparseBigram.train(inv,((0,1,0,2,1,0,2,3),(2,0,1,3,0,1)))
    yield inv,ShuffleContrast(base,shuffles=3,seed=2701)
    inv.close()


def test_signed_margins_and_direct_ll_contrast(model):
    _,m=model
    for doc in ((0,),(0,1),(0,1,2),(0,1,0,2,3,1,0)):
        pairs=m.pairs(doc);incoming=Counter();outgoing=Counter()
        for (a,b),n in pairs.items():incoming[b]+=n;outgoing[a]+=n
        assert all(n==0 for n in incoming.values()) and all(n==0 for n in outgoing.values())
        null=[tuple(doc[i] for i in order) for order in permutations(len(doc),m.shuffles,m.seed)]
        expected=m.bigram.score(doc)-math.fsum(m.bigram.score(d) for d in null)/m.shuffles
        assert m.score(doc)==pytest.approx(expected,abs=1e-11)
        assert m.score_chunks((doc[:1],doc[1:]))==m.score(doc)
    assert m.score((4,5,6,5,4,7,4))==0.
    with pytest.raises(ValueError):m.score(())


def test_exact_dictionary_deltas_including_multiple_documents(model):
    _,m=model
    stream=CipherStream(((0,1,0,2,1,2,0),(2,0,1),(1,)),3)
    for key in keys(range(5),3):
        scorer=DictionaryScorer(m,stream,DictionaryState.create(stream,m,key))
        assert scorer.score==pytest.approx(full_score(m,stream,scorer.state))
        for c,w in product(range(3),range(5)):
            move=scorer.assign_or_swap(c,w);new=list(key)
            for a,b in move.changes:new[a]=b
            assert move.log_delta==pytest.approx(full_score(m,stream,DictionaryState.create(stream,m,new))-scorer.score,abs=1e-10)
        cycle=scorer.propose({0:key[1],1:key[2],2:key[0]})
        scorer.commit(cycle);scorer.validate()
    other=ShuffleContrast(m.bigram,shuffles=3,seed=9901)
    with pytest.raises(ValueError):DictionaryScorer(other,stream,scorer.state,event_index=scorer.index)


def test_serialization_checkpoint_and_context_ranking(model,tmp_path):
    inv,m=model
    path=tmp_path/'model.sqlite';m.save(path);loaded=load_model(path,inv)
    assert m.identity==loaded.identity and m.score((0,1,0,2,0))==loaded.score((0,1,0,2,0))
    context=ContextIndex(m,limit=3)
    for neighbor in (0,1,2,3):
        expected=tuple(sorted(range(m.size),key=lambda w:(-m.pair_value(neighbor,w),w))[:3])
        # All positive-context words must be retrieved; zero-evidence fillers
        # retain the existing base-frequency fallback ordering.
        got=context.query('successors',neighbor)
        assert {w for w in expected if m.pair_value(neighbor,w)>0}<={*got}
    stream=CipherStream(((0,1,0,2,0,1,2),),3)
    search=DictionarySearch(m,stream,seed=3,config=SearchConfig(proposals=20),
              retrieval_config=RetrievalConfig(active_limit=5,total_entries=20,per_context=3))
    for _ in range(8):search.advance()
    path=tmp_path/'checkpoint.json';search.save(path);resumed=DictionarySearch.load(path,loaded,stream)
    for _ in range(12):assert search.advance()==resumed.advance()
    assert search.joint_archive==resumed.joint_archive
    resumed.scorer.validate()


def test_regularized_contrast_exact_formula_moves_and_identity(model,tmp_path):
    inventory,pure=model
    model=ShuffleContrast(pure.bigram,shuffles=pure.shuffles,frequency_weight=.25)
    doc=(0,1,0,2,3,1,0)
    assert model.score(doc)==pytest.approx(pure.score(doc)+.25*sum(math.log(pure.base_probability(w)) for w in doc))
    assert model.identity!=pure.identity
    stream=CipherStream(((0,1,0,2,1,2,0),(2,0,1),(1,)),3)
    for key in keys(range(5),3):
        scorer=DictionaryScorer(model,stream,DictionaryState.create(stream,model,key))
        for c,w in product(range(3),range(5)):
            move=scorer.assign_or_swap(c,w);new=list(key)
            for a,b in move.changes:new[a]=b
            assert move.log_delta==pytest.approx(full_score(model,stream,DictionaryState.create(stream,model,new))-scorer.score,abs=1e-10)
    path=tmp_path/'regularized.sqlite';model.save(path);loaded=load_model(path,inventory)
    assert loaded.identity==model.identity and loaded.score(doc)==model.score(doc)
    with pytest.raises(ValueError):ShuffleContrast(pure,frequency_weight=.25)


def test_permutations_are_independent_of_symbol_names():
    doc=(0,1,2,0,3,1,2,4,0,2,1)
    rename={0:97,1:41,2:12,3:103,4:8}
    expected={(rename[a],rename[b]):n for (a,b),n in signed_pairs(doc).items()}
    assert signed_pairs(tuple(rename[x] for x in doc))==expected
