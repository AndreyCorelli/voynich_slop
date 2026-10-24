import itertools
import numpy as np
from scipy.optimize import minimize
from voynich_smt.latent_cipher_classes import fixed_chain,forward_backward,prior_data,update,log_prior
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_log_prior,supported_step


def test_full_support_reproduces_original_priors_and_update():
    seq=[[0,1,0,2],[3,2]];end=[0,0,1,1];mask=np.ones((2,4),bool);counts=np.array([[2.,1,0,0],[0,0,2,1]])
    p=supported_prior(seq,end,mask);q,qe,within=prior_data(seq,end)
    for sharing in (False,True):
        e=supported_update(counts,p,sharing);expected=update(counts,end,q,qe,within,sharing)
        np.testing.assert_allclose(e,expected);np.testing.assert_allclose(supported_log_prior(e,p,sharing),log_prior(e,end,q,qe,within,sharing))


def test_constrained_m_step_against_independent_optimizer():
    seq=[[0,1,0,2,3]];end=[0,0,1,2];mask=np.array([[1,1,0,0],[0,1,1,1]],bool);counts=np.array([[2.,.2,0,0],[0,.8,1.,1.]])
    p=supported_prior(seq,end,mask)
    for sharing in (False,True):
        fitted=supported_update(counts,p,sharing);np.testing.assert_allclose(fitted.sum(axis=1),1);assert not fitted[~mask].any()
        def objective(e):return sum(float(np.sum(row[row>0]*np.log(erow[row>0]))) for row,erow in zip(counts,e))+supported_log_prior(e,p,sharing)
        def decode(x):
            e=np.zeros_like(counts);offset=0
            for i,s in enumerate(mask):
                n=int(s.sum());v=np.exp(x[offset:offset+n]-max(x[offset:offset+n]));e[i,s]=v/v.sum();offset+=n
            return e
        result=minimize(lambda x:-objective(decode(x)),np.zeros(mask.sum()),method='BFGS',options={'gtol':1e-8})
        np.testing.assert_allclose(objective(fitted),-result.fun,atol=1e-7)


def test_zero_emissions_match_exhaustive_paths():
    seqs=[[0],[1,2,1]];chain=fixed_chain([[0,1,0],[1,1]],2);e=np.array([[.7,.3,0],[0,.4,.6]])
    ll,gamma=forward_backward(chain,e,seqs);expected=0
    for seq,g in zip(seqs,gamma):
        paths=list(itertools.product(range(2),repeat=len(seq)));weights=[]
        for path in paths:
            w=chain['start'][path[0]]*chain['stop'][path[-1]]
            for i,(s,word) in enumerate(zip(path,seq)):
                w*=e[s,word]
                if i:w*=chain['transition'][path[i-1]][s]
            weights.append(w)
        z=sum(weights);expected+=np.log(z);posterior=np.zeros_like(g)
        for path,w in zip(paths,weights):
            for i,s in enumerate(path):posterior[i,s]+=w/z
        np.testing.assert_allclose(g,posterior,atol=1e-12)
    np.testing.assert_allclose(ll,expected)


def test_supported_em_monotonic_and_inactive_endings():
    seq=[[0,1,2],[1,2,3],[0,3]];end=[0,0,1,2];mask=np.array([[1,1,0,0],[0,1,1,1]],bool);chain=fixed_chain([[0,1,1],[0,0,1]],2);p=supported_prior(seq,end,mask)
    for sharing in (False,True):
        e=supported_update(np.array([[1.,1,0,0],[0,1.,1.,1.]]),p,sharing);old=-np.inf
        for _ in range(20):
            ll,g=forward_backward(chain,e,seq);objective=ll+supported_log_prior(e,p,sharing);assert objective>=old-1e-10;old=objective
            assert not e[~mask].any();np.testing.assert_allclose(e.sum(axis=1),1)
            e=supported_step(chain,e,seq,p,sharing)
