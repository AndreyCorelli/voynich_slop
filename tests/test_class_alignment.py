import copy
import numpy as np
import pytest
from voynich_smt.class_alignment import (maps,encode,fit_source,align,shuffle_context,statistics,tag_class,score_maps)
from benchmarks.grammar_class_alignment_iteration25 import OUT,load,proxy_groups
from benchmarks.grammar_class_alignment_iteration25_evaluate import metrics,oracle_maps


def test_search_spaces_are_complete():
    assert len(maps(3,3,True))==6 and len(maps(8,8,True))==40320 and len(maps(8,3,False))==6561
    assert all(sorted(row)==[0,1,2] for row in maps(3,3,True))


def test_transition_model_recovers_hidden_classes():
    sentences=[[0,1,2,1,0]]*30;source=fit_source(sentences,3);anonymous,key=encode(sentences,3,123)
    inferred=align(source,anonymous,3)
    assert inferred['markov']['mapping']==key
    assert inferred['markov']['optimal_maps']==1


def test_symmetric_classes_remain_unresolved():
    sentences=[[0,1],[1,0]]*10;source=fit_source(sentences,2);result=align(source,sentences,2)
    for method in result.values():
        assert method['optimal_maps']==2 and method['mapping']==[None,None]
        assert method['options']==[[0,1],[0,1]]


def test_rekey_preserves_noisy_semantic_observations():
    sentences=[list(range(8))*20 for _ in range(10)]
    a,ia=encode(sentences,8,123,noise=.25);b,ib=encode(sentences,8,321,noise=.25)
    assert a!=b
    aa=[[ia[x] for x in seq] for seq in a];bb=[[ib[x] for x in seq] for seq in b]
    assert aa==bb and aa!=sentences


def test_noise_replaces_by_another_class():
    sentences=[[0,1,2]*10];a,inverse=encode(sentences,3,4,noise=1)
    assert all(inverse[x]!=y for seq,gold in zip(a,sentences) for x,y in zip(seq,gold))


def test_shuffling_keeps_frequency_but_changes_transitions():
    seq=[[0,1,2,1,0]]*20;a=statistics(seq,3);b=statistics(shuffle_context(seq),3)
    assert np.array_equal(a['unigram'],b['unigram']) and not np.array_equal(a['transition'],b['transition'])


def test_frequency_objective_is_invariant_to_order_control():
    seq=[[0,1,2,1,0]]*20;source=fit_source(seq,3)
    _,a,_=score_maps(source,seq,3,True);_,b,_=score_maps(source,shuffle_context(seq),3,True)
    assert np.array_equal(a['frequency'],b['frequency'])


def test_missing_class_does_not_force_an_unsupported_unique_name():
    source=fit_source([[0]*10]*20,3);result=align(source,[[0]*10],3)
    assert result['frequency']['mapping'][0]==0
    assert result['frequency']['mapping'][1:]==[None,None]


def test_many_to_one_likelihood_can_collapse_classes():
    source=fit_source([[0]*10]*20,3);result=align(source,[[0,1,2,1,0]]*4,3,bijective=False)
    assert result['markov']['mapping']==[0,0,0]


def test_proxy_ceiling_exposes_mixed_classes():
    table=np.array([[3,3,0],[0,0,6]])
    oracle=oracle_maps(table,False)
    assert oracle['accuracy']['metrics']['accuracy']<1
    assert oracle['balanced_accuracy']['metrics']['balanced_accuracy']==pytest.approx(2/3)


def test_proxy_is_word_rename_invariant():
    a=[{'tokens':['a','b','a','c']},{'tokens':['c','d','a']}]
    rename={'a':'zzz','b':'xxx','c':'q','d':'longer'}
    b=[{'tokens':[rename[w] for w in s['tokens']]} for s in a]
    assert proxy_groups(a)==proxy_groups(b)


def test_evaluation_labels_do_not_enter_alignment():
    observations=load(OUT/'observations.json');models=load(OUT/'models.json')
    from benchmarks.grammar_class_alignment_iteration25 import produce
    obs=copy.deepcopy(observations[:1]);first=produce(models,obs)
    obs[0]['target_labels']=[['FAKE']];obs[0]['inverse_key']=['FAKE']
    assert produce(models,obs)==first


def test_clean_oracle_class_mapping_is_recovered_on_both_tests():
    rows=load(OUT/'evaluation.json')
    clean=[r for r in rows if r['template']=='pooled' and r['condition']=='ordered' and r['noise']==0 and r['family'] in ('coarse','fine')]
    assert len(clean)==4
    assert all(r['methods']['markov']['accuracy']==1 and r['methods']['markov']['key_accuracy_observed']==1 for r in clean)


def test_proxy_oracle_is_not_an_actual_class_inducer():
    rows=load(OUT/'evaluation.json')
    proxy=[r for r in rows if r['template']=='pooled' and r['condition']=='ordered' and r['family']=='frequency_proxy']
    assert len(proxy)==2 and all(r['oracle']['balanced_accuracy']['metrics']['balanced_accuracy']<.6 for r in proxy)


def test_wrong_objective_can_beat_available_correct_key():
    rows=load(OUT/'evaluation.json')
    row=next(r for r in rows if r['template']=='pooled' and r['family']=='fine' and r['split']=='test_jerome' and r['noise']==0 and r['condition']=='ordered')
    assert row['methods']['frequency']['known_key_strictly_outscored']
    assert row['methods']['frequency']['score']>row['methods']['frequency']['known_key_score']
    assert not row['methods']['markov']['known_key_strictly_outscored']


def test_unknown_mapping_is_abstention_not_class_zero():
    result=metrics([None,0],np.array([[4,0],[0,6]]))
    assert result['coverage']==.6 and result['accuracy']==0 and result['covered_accuracy']==0
