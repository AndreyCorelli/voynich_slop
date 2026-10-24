from collections import Counter

from benchmarks.scalable_english_diagnostics import attribution, decomposition
from benchmarks.scalable_english_trace import replay
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
from voynich_smt.word_mapping.scalable.search import DictionarySearch, SearchConfig
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram


def test_failure_categories_are_disjoint_and_track_displacement():
    events=[{'kind':'initial','assignments':[7,8,9,10,11,12,6]},
            {'kind':'pool','cipher':3,'offered':[(10,0),(3,-1)],'active':[10]},
            {'kind':'pool','cipher':4,'offered':[(11,0),(4,-1)],'active':[11,4]},
            {'kind':'move','cipher':5,'word_id':5,'changes':[(5,5)],'accepted':False},
            {'kind':'move','cipher':1,'word_id':1,'changes':[(1,1)],'accepted':True},
            {'kind':'move','cipher':6,'word_id':13,'changes':[(6,13)],'accepted':True}]
    result=attribution(events,[None,1,2,3,4,5,6],[7,1,9,10,11,12,13],Counter({i:1 for i in range(7)}))
    assert result['categories']=={'inventory_absent':1,'recovered':1,'never_offered':1,
        'offered_not_active':1,'active_not_chosen':1,'proposed_not_accepted':1,'acquired_then_lost':1}
    assert result['rows'][6]['correct_assignment_displacements']==1


def test_offered_and_actual_swaps_credit_the_indirect_assignment():
    events=[{'kind':'initial','assignments':[2,1]},
            {'kind':'pool','cipher':0,'offered':[(2,0),(1,1)],'active':[2,1]},
            {'kind':'move','cipher':0,'word_id':1,'changes':[(0,1),(1,2)],'accepted':True}]
    result=attribution(events,[0,2],[1,2],Counter({0:2,1:1}))
    assert result['rows'][1]['offered'] and result['rows'][1]['active']
    assert result['rows'][1]['accepted'] and not result['rows'][1]['visited']
    assert result['categories']['recovered']==1


def test_observational_replay_preserves_rng_decisions_and_archives(tmp_path):
    inventory=Inventory.build(tmp_path/'inventory.sqlite',['a','b','c','d'])
    try:
        model=SparseBigram.train(inventory,[[0,1,0,2],[1,2,0]])
        stream=CipherStream(((0,1,0,2),),3)
        options=dict(seed=3,config=SearchConfig(proposals=40),
                     retrieval_config=RetrievalConfig(active_limit=4,total_entries=12))
        plain=DictionarySearch(model,stream,**options)
        expected=[plain.advance() for _ in range(40)]
        traced=DictionarySearch(model,stream,**options)
        events=[]
        replay(traced,40,events.append)
        actual=[{k:e[k] for k in expected[0]} for e in events if e['kind']=='move']
        assert actual==expected
        assert plain.joint_archive==traced.joint_archive
        assert plain.rng.getstate()==traced.rng.getstate()
        assert plain.retriever.rng.getstate()==traced.retriever.rng.getstate()
        decomposition_result=decomposition(model,stream,plain.joint_archive[0][1])
        assert abs(decomposition_result['base_frequency_component']+decomposition_result['context_component']-decomposition_result['source_score'])<1e-12
    finally:inventory.close()
