import copy
import numpy as np
import pytest
from voynich_smt.cipher_relations import (ARMS,RADIUS,views,encrypt,candidates,pair_features,masked_number_features,
    matrix,fit,probabilities,decode,token_features)
from benchmarks.grammar_cipher_relations_iteration23 import relation_matrix,number_matrix,OUT,load
from benchmarks.grammar_cipher_relations_iteration23_evaluate import relation_metrics,fingerprint

SENTENCES=[{'tokens':['puella','bona','puellam','puella']},{'tokens':['mater','puellam','amat']}]
LATTICE={'puella':[{'pos':'N','features':[['Case','NOM'],['Gender','F'],['Number','S']]}],
    'bona':[{'pos':'ADJ','features':[['Case','NOM'],['Gender','F'],['Number','S']]}],
    'puellam':[{'pos':'N','features':[['Case','ACC'],['Number','S']]}]}

@pytest.mark.parametrize('arm',ARMS)
def test_key_invariance(arm):
    first=views(SENTENCES,11,LATTICE);second=views(SENTENCES,29,LATTICE)
    for a,b in zip(first,second):
        assert a['tokens']!=b['tokens']
        for c,p in candidates(len(a['tokens'])):assert pair_features(a,c,p,arm)==pair_features(b,c,p,arm)
        for p in range(len(a['tokens'])):assert masked_number_features(a,p,arm)==masked_number_features(b,p,arm)


def test_bijective_fixed_length_cipher_preserves_repetition_and_suffix_classes():
    sequences,mapping=encrypt(SENTENCES,3)
    assert len(set(mapping.values()))==len(mapping)
    assert {len(w) for w in mapping.values()}=={12}
    assert sequences[0][0]==sequences[0][3]
    _,shared=encrypt([{'tokens':['puella','stella']}],3)
    assert shared['puella'][-2:]==shared['stella'][-2:]
    assert mapping['puella'][-2:]!=mapping['puellam'][-2:]

@pytest.mark.parametrize('arm',['geometry','repetition','ending_blind'])
def test_blind_channels_do_not_use_privileged_metadata(arm):
    view=views(SENTENCES,2,LATTICE)[0];erased=copy.deepcopy(view);erased['metadata']={}
    for c,p in candidates(len(view['tokens'])):assert pair_features(view,c,p,arm)==pair_features(erased,c,p,arm)


def test_exposed_and_dictionary_channels_are_explicit():
    v=views(SENTENCES,2,LATTICE)[0]
    assert 'latin_ending=la' in token_features(v,0,'ending_exposed')
    assert 'm:Case=NOM' in token_features(v,0,'dictionary')
    assert not any('latin_ending' in x or x.startswith('m:') for x in token_features(v,0,'ending_blind'))

@pytest.mark.parametrize('arm',ARMS)
def test_own_word_type_is_masked_in_number_contexts(arm):
    v=views(SENTENCES,2,LATTICE)[0];poison=copy.deepcopy(v);word=v['tokens'][0]
    poison['metadata'][word]={'exposed_suffix':'zz','morph':{'pos':{'FAKE'},'Number':{'P'}}}
    assert masked_number_features(v,0,arm)==masked_number_features(poison,0,arm)
    local=views([{'tokens':['puella','puella','bona']}],2,LATTICE)[0]
    assert 'context1:masked' in masked_number_features(local,0,arm)


def test_relation_features_do_not_see_labels_or_reference_positions():
    a=[{'tokens':['puella','bona','puellam','puella'],'edges':[[1,0,3]],'finite':[2]}]
    b=[{'tokens':a[0]['tokens'],'edges':[[0,2,1]],'finite':[0]}]
    v=views(a,1,LATTICE)
    for arm in ARMS:
        x,y,_,_=relation_matrix(a,v,arm);xx,yy,_,_=relation_matrix(b,v,arm)
        assert fingerprint(x)==fingerprint(xx) and y!=yy


def test_number_labels_do_not_enter_features():
    a=[{'sent_id':'x','tokens':SENTENCES[0]['tokens'],'numbers':[[0,0],[1,1]]}]
    b=copy.deepcopy(a);b[0]['numbers']=[[0,1],[1,0]];v=views(a,2,LATTICE)
    for arm in ARMS:
        x,y,q=number_matrix(a,v,arm);xx,yy,qq=number_matrix(b,v,arm)
        assert fingerprint(x)==fingerprint(xx) and y!=yy and q==qq


def test_gold_outside_radius_is_still_counted():
    gold=[{'tokens':['x']*(RADIUS+2),'edges':[[0,RADIUS+1,1]]}]
    metrics=relation_metrics([{'edges':[]}],gold)
    assert metrics['micro']['gold']==1 and metrics['radius_reachable_gold']==0
    assert all(c!=p and abs(c-p)<=RADIUS for c,p in candidates(RADIUS+2))


def test_decode_has_at_most_one_head_but_cycle_is_reported():
    pairs=[(0,1),(0,2),(1,0)]
    values=np.array([[.1,.9,0,0,0],[.1,0,.9,0,0],[.1,.9,0,0,0]])
    edges=decode(pairs,values,.5)
    assert len({e[0] for e in edges})==len(edges)==2
    metrics=relation_metrics([{'edges':edges}],[{'edges':[],'tokens':['a','b','c']}])
    assert metrics['sentences_with_predicted_cycle']==1


def test_sparse_classifier_learns_simple_separable_case():
    x=matrix([['bias','left'],['bias','left'],['bias','right'],['bias','right']]);y=[0,0,1,1]
    model=fit(x,y,2);p=probabilities(x,model)
    assert np.array_equal(p.argmax(axis=1),y)
    assert np.allclose(p.sum(axis=1),1) and model['loss']<np.log(2)


def test_split_and_cipher_checks_are_saved():
    data=load(OUT/'datasets.json');ids=[{s['sent_id'] for s in ss} for ss in data.values()]
    assert all(not a&b for i,a in enumerate(ids) for j,b in enumerate(ids) if i<j)
    assert {s['author'] for s in data['test_caesar']}=={'Caesar'}
    assert 'Caesar' not in {s['author'] for s in data['train']+data['tune']}
    assert len(load(OUT/'rekey-checks.json'))==20


def test_transfer_uses_only_compatible_relation_types_and_excludes_masked_type():
    data=load(OUT/'datasets.json')
    for row in load(OUT/'agreement-transfer-predictions.json'):
        lookup={s['sent_id']:s for s in data[row['split']]}
        for r in row['records']:
            if not r['covered']:continue
            s=lookup[r['sent_id']];parent=r['edge'][1]
            assert r['edge'][2] in (1,3) and parent!=r['position']
            assert s['tokens'][parent]!=s['tokens'][r['position']]
            assert r['guess']==dict(s['numbers'])[parent]


def test_matched_context_control_keeps_coverage():
    transfer=load(OUT/'agreement-transfer.json');control=load(OUT/'agreement-transfer-control.json')
    for key,row in control.items():
        assert row['queries']==transfer[key]['queries']
        assert row['covered_queries']==round(transfer[key]['coverage']*row['queries'])
        assert 0<=row['random_context_expected_full_balanced_accuracy']<=1
