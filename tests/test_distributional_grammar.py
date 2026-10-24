import copy
import numpy as np
import pytest
from voynich_smt.cipher_relations import views
from voynich_smt.distributional_grammar import (observations,profiles,fit_prototypes,attach_profiles,
    pair_features,consensus,skeleton,wilson_lower,CONTEXT_DIM)
from benchmarks.grammar_distributional_skeleton_iteration24 import calibrate
from benchmarks.grammar_distributional_skeleton_iteration24_evaluate import fragments

CORPUS=[{'tokens':['alpha','beta','alpha','gamma']} for _ in range(4)]+[{'tokens':['gamma','beta','gamma','alpha']} for _ in range(3)]


def test_leave_sentence_out_removes_all_own_observations():
    v=views(CORPUS,10,{})
    obs=observations(v);word=v[0]['tokens'][0]
    wp,ep,ws,es=profiles(obs,word,0);localw,locale,localglobal=obs['sentences'][0]
    w=obs['words'][word]-localw[word];e=obs['endings'][word[-2:]]-locale[word[-2:]];g=obs['global_count']-localglobal;g/=g.sum()
    expected_e=(e+4*g)/(e.sum()+4);expected_w=(w+4*expected_e)/(w.sum()+4)
    assert np.allclose(ep,expected_e) and np.allclose(wp,expected_w)
    assert ws==w.sum() and es==e.sum()


def test_single_sentence_cannot_supply_its_own_profile():
    v=views(CORPUS[:1],10,{});obs=observations(v)
    for word in v[0]['tokens']:
        wp,ep,ws,es=profiles(obs,word,0)
        assert ws==es==0
        assert np.allclose(wp,np.full(CONTEXT_DIM,1/CONTEXT_DIM)) and np.allclose(ep,wp)

@pytest.mark.parametrize('shuffle',[False,True])
def test_context_profiles_are_cipher_key_invariant(shuffle):
    a=views(CORPUS,10,{});b=views(CORPUS,44,{})
    pa=fit_prototypes(observations(a,shuffle=shuffle));pb=fit_prototypes(observations(b,shuffle=shuffle));assert pa==pb
    av=attach_profiles(a,pa,shuffle=shuffle);bv=attach_profiles(b,pa,shuffle=shuffle)
    for first,second in zip(av,bv):assert pair_features(first,0,1,'profiles')==pair_features(second,0,1,'profiles')


def test_profiles_do_not_use_privileged_metadata():
    v=views(CORPUS,10,{});prototype=fit_prototypes(observations(v));before=attach_profiles(v,prototype)
    erased=copy.deepcopy(v)
    for row in erased:row['metadata']={}
    after=attach_profiles(erased,prototype)
    for a,b in zip(before,after):assert pair_features(a,0,1,'profiles')==pair_features(b,0,1,'profiles')


def test_shuffle_preserves_counts_but_changes_context():
    v=views(CORPUS,10,{});a=observations(v);b=observations(v,shuffle=True)
    assert set(a['words'])==set(b['words']) and set(a['endings'])==set(b['endings'])
    assert a['global_count'].sum()==b['global_count'].sum()
    assert any(not np.array_equal(a['words'][w],b['words'][w]) for w in a['words'])


def test_consensus_requires_same_head_and_label():
    pairs=[(0,1),(0,2)];a=np.array([[.1,.8,.05,.03,.02],[.8,.05,.05,.05,.05]])
    b=np.array([[.8,.05,.05,.05,.05],[.1,.8,.05,.03,.02]])
    assert len(consensus(pairs,[a,a,a]))==1
    assert consensus(pairs,[a,a,b])==[]
    c=a.copy();c[0]=[.1,.05,.8,.03,.02]
    assert consensus(pairs,[a,a,c])==[]


def test_numeric_ties_are_abstentions():
    p=np.array([[.1,.8,.05,.03,.02],[.1,.8,.05,.03,.02]])
    assert consensus([(0,1),(0,2)],[p,p,p])==[]


def test_skeleton_drops_lowest_confidence_cycle_edge():
    edges=[[0,1,1,.9,.2],[1,2,1,.8,.2],[2,0,1,.7,.2]]
    assert skeleton(edges,.5,.1)==edges[:2]


def test_skeleton_abstains_without_forced_completion():
    assert skeleton([[0,1,1,.6,.01]],.5,.1)==[]
    assert skeleton([[0,1,1,.6,.2]],.9,.1)==[]
    assert skeleton([],0,0)==[]


def test_precision_calibration_can_decline_all_targets():
    sentences=[{'edges':[[0,1,1]]} for _ in range(25)]
    wrong=[[[0,1,2,.9,.2]] for _ in range(25)]
    grid,policies=calibrate(wrong,sentences)
    assert all(not p['enabled'] for key,p in policies.items() if key.startswith('precision'))


def test_precision_calibration_needs_enough_evidence():
    sentences=[{'edges':[[0,1,1]]} for _ in range(5)];correct=[[[0,1,1,.9,.2]] for _ in range(5)]
    _,policies=calibrate(correct,sentences)
    assert not policies['precision_0.5']['enabled']
    _,policies=calibrate(correct*10,sentences*10)
    assert policies['precision_0.85']['enabled']
    assert wilson_lower(0,0)==0 and wilson_lower(20,20)<.85


def test_complete_shared_head_fragment_needs_both_edges():
    assert fragments([[0,1,1,.9,.2]])==set()
    assert fragments([[0,1,1,.9,.2],[2,1,2,.8,.2]])=={(0,1,2)}
    assert fragments([[0,1,1],[2,3,2]])==set()


def test_gold_properties_do_not_change_anonymous_observations():
    labeled=[{**s,'properties':{'upos':['NOUN']*len(s['tokens'])},'edges':[[0,1,1]]} for s in CORPUS]
    poisoned=[{**s,'properties':{'upos':['VERB']*len(s['tokens'])},'edges':[[1,0,2]]} for s in CORPUS]
    a=observations(views(labeled,10,{}));b=observations(views(poisoned,10,{}))
    assert fit_prototypes(a)==fit_prototypes(b)


def test_saved_backgrounds_and_precision_abstentions():
    from benchmarks.grammar_distributional_skeleton_iteration24 import OUT,load
    data=load(OUT/'datasets.json');models=load(OUT/'models.json')
    for split,ss in data.items():
        if split.startswith('background'):assert all('edges' not in s and 'properties' not in s for s in ss)
    for arm in ('baseline','profiles','shuffled_profiles'):
        assert all(not p['enabled'] for name,p in models[arm]['operating'].items() if name.startswith('precision'))


def test_information_audit_detects_label_independence_and_identity():
    from benchmarks.grammar_distributional_skeleton_iteration24_diagnostics import mutual_information
    assert abs(mutual_information(['a','a','b','b'],['S','P','S','P']))<1e-10
    assert abs(mutual_information(['a','a','b','b'],['S','S','P','P'])-1)<1e-10
