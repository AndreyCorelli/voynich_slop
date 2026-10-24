import itertools
import numpy as np
from voynich_smt.latent_cipher_classes import fixed_chain,forward_backward
from voynich_smt.budgeted_candidate_repair import repair_prior,anchored_emission,repair_step,repair_log_prior


def test_normalization_inactive_state_and_zero_budget():
    base=np.array([[.2,.3,.5],[.6,.1,.3]]);repair=np.array([[0.,1,0],[0,0,0]])
    old=base.copy();e=anchored_emission(base,repair,.01);np.testing.assert_allclose(e.sum(axis=1),1);np.testing.assert_array_equal(e[1],base[1]);np.testing.assert_array_equal(anchored_emission(base,repair,0),base);np.testing.assert_array_equal(base,old)
    np.testing.assert_allclose(e[0],.99*base[0]+.01*repair[0])


def test_unrepaired_word_class_odds_bound():
    base=np.array([[.2,.3,.5],[.6,.1,.3]]);repair=np.array([[0.,1,0],[0,0,0]]);delta=.1;e=anchored_emission(base,repair,delta)
    for word in (0,2):
        ratio=(e[0,word]/e[1,word])/(base[0,word]/base[1,word]);assert 1-delta-1e-12<=ratio<=1/(1-delta)+1e-12


def test_repair_channel_expected_counts_against_enumeration():
    chain=fixed_chain([[0,1,0],[1,1]],2);seq=[[0,1,2]];base=np.array([[.6,.3,.1],[.2,.2,.6]]);repair=np.array([[0,.7,.3],[.4,0,.6]]);prior=repair_prior([.4,.4,.2],repair>0);delta=.1;counts=np.zeros_like(repair);configurations=list(itertools.product(range(4),repeat=3));weights=[]
    for config in configurations:
        states=[x//2 for x in config];p=chain['start'][states[0]]*chain['stop'][states[-1]]
        for i,(x,w) in enumerate(zip(config,seq[0])):
            s=x//2;p*=delta*repair[s,w] if x%2 else (1-delta)*base[s,w]
            if i:p*=chain['transition'][states[i-1]][s]
        weights.append(p)
    for config,p in zip(configurations,weights):
        for x,w in zip(config,seq[0]):
            if x%2:counts[x//2,w]+=p/sum(weights)
    expected=counts+prior;expected/=expected.sum(axis=1,keepdims=True)
    np.testing.assert_allclose(repair_step(chain,base,repair,seq,prior,delta),expected,atol=1e-12)
    ll,_=forward_backward(chain,anchored_emission(base,repair,delta),seq);np.testing.assert_allclose(ll,np.log(sum(weights)),atol=1e-12)


def test_em_monotonic_and_old_table_immutable():
    base=np.array([[.6,.3,.1],[.2,.2,.6]]);copy=base.copy();mask=np.array([[0,1,1],[1,0,1]],bool);prior=repair_prior([.4,.4,.2],mask);repair=prior.copy();chain=fixed_chain([[0,1,0],[1,1]],2);seq=[[0,1,2],[0,2],[1,1]];old=-np.inf
    for _ in range(40):
        e=anchored_emission(base,repair,.1);ll,_=forward_backward(chain,e,seq);obj=ll+repair_log_prior(repair,prior);assert obj>=old-1e-10;old=obj
        assert not repair[~mask].any();repair=repair_step(chain,base,repair,seq,prior,.1)
    np.testing.assert_array_equal(base,copy)
