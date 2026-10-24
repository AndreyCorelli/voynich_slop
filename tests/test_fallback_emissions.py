import itertools
import numpy as np
import pytest
from voynich_smt.latent_cipher_classes import fixed_chain,forward_backward,prior_data
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_step,supported_log_prior
from voynich_smt.fallback_emissions import mixture,mixture_step,fallback_posteriors


def test_normalization_floor_and_zero_limit():
    component=np.array([[.7,.3,0],[0,.2,.8]]);q=np.array([.5,.3,.2]);e=mixture(component,q,.1)
    np.testing.assert_allclose(e.sum(axis=1),1);assert np.all(e>=.1*q);np.testing.assert_array_equal(mixture(component,q,0),component)
    with pytest.raises(ValueError):mixture(component,q,1)


def test_latent_channel_m_step_against_enumeration():
    seqs=[[0,1,2]];ends=[0,0,1];support=np.array([[1,1,0],[0,1,1]],bool);chain=fixed_chain([[0,1,0],[1,1]],2);component=np.array([[.7,.3,0],[0,.4,.6]]);q=prior_data(seqs,ends)[0];prior=supported_prior(seqs,ends,support);epsilon=.2
    weights=[];configurations=list(itertools.product(range(4),repeat=3))
    for config in configurations:
        states=[x//2 for x in config];channels=[x%2 for x in config];p=chain['start'][states[0]]*chain['stop'][states[-1]]
        for i,(s,c,w) in enumerate(zip(states,channels,seqs[0])):
            p*=epsilon*q[w] if c else (1-epsilon)*component[s,w]
            if i:p*=chain['transition'][states[i-1]][s]
        weights.append(p)
    z=sum(weights);counts=np.zeros_like(component);fallback=np.zeros(3)
    for config,p in zip(configurations,weights):
        for i,(x,w) in enumerate(zip(config,seqs[0])):
            if x%2:fallback[i]+=p/z
            else:counts[x//2,w]+=p/z
    for sharing in (False,True):np.testing.assert_allclose(mixture_step(chain,component,seqs,prior,q,epsilon,sharing),supported_update(counts,prior,sharing),atol=1e-12)
    ll,gamma=forward_backward(chain,mixture(component,q,epsilon),seqs)
    np.testing.assert_allclose(ll,np.log(z));np.testing.assert_allclose(fallback_posteriors(component,q,epsilon,seqs,gamma),fallback,atol=1e-12)


def test_zero_epsilon_reproduces_hard_update():
    seqs=[[0,1,2],[1,2]];ends=[0,0,1];support=np.array([[1,1,0],[0,1,1]],bool);chain=fixed_chain([[0,1],[1,0]],2);prior=supported_prior(seqs,ends,support);q=prior_data(seqs,ends)[0];c=np.array([[.7,.3,0],[0,.3,.7]])
    for sharing in (False,True):np.testing.assert_allclose(mixture_step(chain,c,seqs,prior,q,0,sharing),supported_step(chain,c,seqs,prior,sharing))


def test_mixture_em_monotonic_with_supported_prior():
    seqs=[[0,1,2],[1,2],[0,2,1]];ends=[0,0,1];support=np.array([[1,1,0],[0,1,1]],bool);chain=fixed_chain([[0,1],[1,0]],2);prior=supported_prior(seqs,ends,support);q=prior_data(seqs,ends)[0]
    for sharing in (False,True):
        component=np.array([[.7,.3,0],[0,.4,.6]]);old=-np.inf
        for _ in range(30):
            emission=mixture(component,q,.1);ll,gamma=forward_backward(chain,emission,seqs);obj=ll+supported_log_prior(component,prior,sharing);assert obj>=old-1e-10;old=obj
            assert not component[~support].any();np.testing.assert_allclose(component.sum(axis=1),1)
            usage=fallback_posteriors(component,q,.1,seqs,gamma);assert np.all((usage>=0)&(usage<=1))
            component=mixture_step(chain,component,seqs,prior,q,.1,sharing)
