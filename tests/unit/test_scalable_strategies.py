from dataclasses import replace
from itertools import permutations, product
import math

import pytest

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer, EventIndex, full_score
from voynich_smt.word_mapping.scalable.retrieval import CandidateRetriever, ContextIndex, RetrievalConfig
from voynich_smt.word_mapping.scalable.search import DictionarySearch, SearchConfig
from voynich_smt.word_mapping.scalable.sparse_lm import BOS, SparseBigram
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.trigram import InterpolatedTrigram, load_model


@pytest.fixture
def resources(tmp_path):
    inventory=Inventory.build(tmp_path/'inventory.sqlite',['a','b','c','d','e'])
    docs=((0,1,2,0,1,2),(3,1,0),(0,),(0,0,1))
    trigram=InterpolatedTrigram.train(inventory,lambda: iter(docs))
    yield inventory,trigram,CipherStream(((0,1,2,0,0,1),(2,),(1,0)),3)
    inventory.close()


def test_trigram_normalization_chunks_and_save(resources,tmp_path):
    inventory,model,_=resources
    identity=model.identity
    for a,b in product(range(BOS,model.size),repeat=2):
        assert sum(model.probability3(a,b,w) for w in range(model.size+1)) == pytest.approx(1)
        assert all(model.probability3(a,b,w)==model._probability3(a,b,w) for w in range(model.size+1))
    assert model.identity==identity
    assert model.lower_probability.cache_info().maxsize==262144
    for words in product(range(3),repeat=3):
        assert model.score_chunks((words[:1],words[1:])) == model.score(words)
    path=tmp_path/'model.sqlite'; model.save(path)
    loaded=load_model(path,inventory)
    assert loaded.identity==model.identity and loaded.order==3
    assert loaded.score([0,1,2,3])==model.score([0,1,2,3])
    # Same bigram projection makes retrieval differences a separate factor.
    assert loaded.edges==model.bigram.edges
    assert loaded.counts==model.bigram.counts
    with pytest.raises(ValueError,match='weight'):
        InterpolatedTrigram(model.bigram,model.triples,weight=0)
    with pytest.raises(ValueError,match='counts differ'):
        InterpolatedTrigram(model.bigram,{})


def test_trigram_local_moves_match_full_stream_and_index_binding(resources):
    _,model,stream=resources
    for key in permutations(range(model.size),3):
        state=DictionaryState.create(stream,model,key)
        scorer=DictionaryScorer(model,stream,state)
        before=full_score(model,stream,state)
        for cipher,word in product(range(3),range(model.size)):
            move=scorer.assign_or_swap(cipher,word)
            new=list(key)
            for c,w in move.changes: new[c]=w
            expected=full_score(model,stream,DictionaryState.create(stream,model,new))-before
            assert move.log_delta==pytest.approx(expected,abs=1e-10)
        cycle=scorer.propose({0:key[1],1:key[2],2:key[0]})
        scorer.commit(cycle); scorer.validate()
    with pytest.raises(ValueError,match='Event index'):
        DictionaryScorer(model,stream,state,event_index=EventIndex.build(stream))


def test_observed_context_queries_and_pooled_capacity(resources):
    _,trigram,stream=resources
    model=trigram.bigram
    index=ContextIndex(model,limit=3)
    for neighbor in range(BOS,model.size):
        actual=index.query('successors_evidence',neighbor)
        expected=sorted([w for a,w in model.edges if a==neighbor and w!=model.eos],
                        key=lambda w:(-model.probability(neighbor,w)/model.base_probability(w),w))[:3]
        assert actual==tuple(expected)
    for neighbor in range(model.size+1):
        actual=index.query('predecessors_evidence',neighbor)
        expected=sorted([w for w,b in model.edges if b==neighbor and w!=BOS],
                        key=lambda w:(-model.probability(w,neighbor),w))[:3]
        assert actual==tuple(expected)
    state=DictionaryState.create(stream,model,[0,1,2])
    config=RetrievalConfig(context_strategy='pooled',active_limit=4,total_entries=8,pool_limit=12,per_context=3)
    retriever=CandidateRetriever(DictionaryScorer(model,stream,state),config=config)
    offered=[]
    for cipher in range(3):
        row=retriever.refresh(cipher,audit=lambda values:offered.extend(values))
        assert row.pool_size<=config.pool_limit
        assert retriever.entry_count<=config.total_entries
    assert any('pooled_context' in candidate.sources for candidate in offered)
    with pytest.raises(ValueError,match='strategy'):
        RetrievalConfig(context_strategy='unknown')


@pytest.mark.parametrize('order',[2,3])
def test_joint_and_pooled_checkpoint_and_observation(resources,tmp_path,order):
    from benchmarks.scalable_english_trace import replay
    _,trigram,stream=resources
    model=trigram if order==3 else trigram.bigram
    options=dict(seed=3,config=SearchConfig(initialization='frequency',proposals=60,joint_probability=.3),
                 retrieval_config=RetrievalConfig(context_strategy='pooled',active_limit=4,total_entries=12,per_context=3))
    search=DictionarySearch(model,stream,**options)
    events=[]
    replay(search,60,events.append)
    assert search.source_counts.get('joint_cycle',0)>0
    partial=DictionarySearch(model,stream,**options)
    first=[partial.advance() for _ in range(17)]
    path=tmp_path/'checkpoint.json'; partial.save(path)
    resumed=DictionarySearch.load(path,model,stream)
    actual=first+[resumed.advance() for _ in range(43)]
    assert actual==[{k:v for k,v in e.items() if k not in ('kind','word_id','changes')}
                    for e in events if e['kind']=='move']
    assert resumed.scorer.state==search.scorer.state
    resumed.scorer.validate()
    for event in events:
        if event['kind']=='move' and event['source']=='joint_cycle':
            assert len(event['changes']) in (0,3)


def test_targeted_cycle_can_escape_pairwise_local_optimum(resources):
    # Search for a concrete complete-key 3-cycle improving while all swaps lose.
    _,model,_=resources
    stream=CipherStream(((0,1,2,0,1,2,0),),3)
    found=False
    for key in permutations(range(model.size),3):
        scorer=DictionaryScorer(model,stream,DictionaryState.create(stream,model,key))
        cycle=scorer.propose({0:key[1],1:key[2],2:key[0]})
        if cycle.log_delta>0 and all(scorer.swap(a,b).log_delta<0 for a,b in ((0,1),(0,2),(1,2))):
            found=True
            break
    # The tested fixture must actually exercise the proposed escape mechanism.
    assert found
    search=DictionarySearch(model,stream,state=scorer.state,
                            config=SearchConfig(joint_probability=.1))
    assert search.joint_proposal(0).log_delta>0


def test_consensus_separates_shared_wrong_prior_from_changed_agreement(tmp_path):
    import gzip
    import json
    from benchmarks.scalable_english_consensus import collect,evaluate
    inventory=Inventory.build(tmp_path/'inventory.sqlite',['a','b','c','d','e'])
    try:
        stream=CipherStream(((0,0,1,2),),3)
        root=tmp_path/'run'; (root/'traces').mkdir(parents=True)
        stream.save(root/'public/cipher.json')
        runs=[]
        for seed,last in ((3,0),(5,3),(7,4)):
            runs.append({'seed':seed,'joint_archive':[{'assignments':[1,2,last]}]})
            with gzip.open(root/f'traces/seed-{seed}.jsonl.gz','wt') as handle:
                handle.write(json.dumps({'kind':'initial','assignments':[1,3,4]})+'\n')
        (root/'inference.json').write_text(json.dumps({'protocol':{
            'cipher_sha256':stream.identity,'inventory_sha256':inventory.identity},'runs':runs}))
        collected=collect(root,root/'consensus-public.json')
        assert collected['rows'][0]['strict_majority']
        assert not collected['rows'][0]['changed_in_all_supporters']
        assert collected['rows'][1]['changed_in_all_supporters']
        truth=tmp_path/'truth.json'
        truth.write_text(json.dumps({'public_sha256':stream.identity,'decoding':['a','c','e']}))
        result=evaluate(tmp_path,root,truth,root/'consensus-evaluation.json')
        assert result['groups']['majority']['type_precision']==.5
        assert result['groups']['majority']['token_precision']==1/3
        assert result['groups']['majority_changed']['type_precision']==1
        assert result['groups']['majority_unchanged_prior']['type_precision']==0
    finally:
        inventory.close()


def test_evaluation_reference_keeps_inventory_and_proxies_missing_words(resources,tmp_path):
    import json
    from benchmarks.scalable_english_objective_reference import reference
    inventory,model,_=resources
    model.save(tmp_path/'model.sqlite')
    stream=CipherStream(((0,1,0),),2)
    public=tmp_path/'public.json'; stream.save(public)
    truth=tmp_path/'truth.json'
    truth.write_text(json.dumps({'public_sha256':stream.identity,'decoding':['a','missing']}))
    result=reference(tmp_path,public,truth)
    assert result['missing_types_proxied']==1
    expected=full_score(model,stream,DictionaryState.create(stream,model,[0,4]))
    assert result['source_score']==expected
    assert result['proxy_alias_check_difference']==0
    reopened=Inventory(tmp_path/'inventory.sqlite')
    assert reopened.identity==inventory.identity
    reopened.close()
    truth.write_text(json.dumps({'public_sha256':stream.identity,'decoding':['missing','alsoabsent']}))
    assert reference(tmp_path,public,truth)['status'].startswith('unavailable')


def test_frequency_tempering_moves_roundtrip_and_resume(resources, tmp_path):
    from voynich_smt.word_mapping.scalable.tempered import FrequencyTempered
    inventory, trigram, stream = resources
    for alpha in (0., .5, 1.):
        model = FrequencyTempered(trigram.bigram, alpha)
        state = DictionaryState.create(stream, model, (0,1,2))
        scorer = DictionaryScorer(model, stream, state)
        words = [state.assignments[c] for c in stream.documents[0]]
        expected = trigram.bigram.score(words)+(alpha-1)*sum(math.log(model.base_probability(w)) for w in words)
        assert model.score(words) == pytest.approx(expected)
        assert model.score_chunks((words[:2],words[2:])) == model.score(words)
        for cipher, word in product(range(3),range(model.size)):
            move = scorer.assign_or_swap(cipher,word)
            key = list(state.assignments)
            for c,w in move.changes: key[c]=w
            assert move.log_delta == pytest.approx(full_score(model,stream,DictionaryState.create(stream,model,key))-scorer.score)
        path = tmp_path/f'tempered-{alpha}.sqlite'; model.save(path)
        loaded = load_model(path,inventory)
        assert loaded.identity == model.identity
        config = SearchConfig(proposals=20,initialization='frequency')
        search = DictionarySearch(loaded,stream,config=config)
        for _ in range(10): search.advance()
        checkpoint = tmp_path/f'checkpoint-{alpha}.json'; search.save(checkpoint)
        resumed = DictionarySearch.load(checkpoint,loaded,stream)
        for _ in range(10): assert search.advance() == resumed.advance()
        search.scorer.validate(); resumed.scorer.validate()
    with pytest.raises(ValueError): FrequencyTempered(trigram.bigram, -1)
