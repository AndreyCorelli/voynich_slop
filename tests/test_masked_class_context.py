import itertools
import numpy as np
from voynich_smt.latent_cipher_classes import fixed_chain
from voynich_smt.masked_class_context import masked_context,local_distribution,probability_metrics


def test_cavity_target_and_neighbors_against_exhaustive_paths():
    chain=fixed_chain([[0,1,2],[2,0,0],[1,2]],3);e=np.array([[.2,.4,.8],[.7,.1,.3],[.4,.9,.2],[.6,.3,.5]]);result=masked_context(chain,e)
    for target in range(len(e)):
        marginal=np.zeros((len(e),3));z=0.
        for path in itertools.product(range(3),repeat=len(e)):
            p=chain['start'][path[0]]*chain['stop'][path[-1]]
            for i,s in enumerate(path):
                if i!=target:p*=e[i,s]
                if i:p*=chain['transition'][path[i-1]][s]
            z+=p
            for i,s in enumerate(path):marginal[i,s]+=p
        marginal/=z;np.testing.assert_allclose(result['posterior'][target],marginal[target],atol=1e-12)
        assert result['left'][target]==(int(marginal[target-1].argmax()) if target else None)
        assert result['right'][target]==(int(marginal[target+1].argmax()) if target+1<len(e) else None)


def test_masked_target_cannot_leak_through_neighbors():
    chain=fixed_chain([[0,1,0],[1,1]],2);e=np.array([[.2,.8],[.9,.1],[.4,.6]])
    original=masked_context(chain,e);changed=e.copy();changed[1]=[100.,.00001];result=masked_context(chain,changed)
    for key in ('posterior','neighbor_distribution'):np.testing.assert_allclose(original[key][1],result[key][1],atol=1e-12)
    assert original['left'][1]==result['left'][1] and original['right'][1]==result['right'][1]


def test_local_boundaries_and_emission_conditioning():
    chain=fixed_chain([[0,1,0],[1,1]],2);t=np.array(chain['transition'])
    for left,right in ((None,None),(None,0),(0,None),(0,1)):
        expected=(np.array(chain['start']) if left is None else t[left])*(np.array(chain['stop']) if right is None else t[:,right])
        np.testing.assert_allclose(local_distribution(chain,left,right),expected/expected.sum())
        e=np.array([.1,.9]);np.testing.assert_allclose(local_distribution(chain,left,right,e),expected*e/(expected*e).sum())
    result=masked_context(chain,np.array([[.1,.9]]));np.testing.assert_allclose(result['posterior'][0],local_distribution(chain));assert result['left']==[None] and result['right']==[None]


def test_probability_metrics_ties_empty_and_balancing():
    p=np.array([[.5,.5],[.1,.9],[.8,.2]]);y=np.array([1,1,0]);m=probability_metrics(p,y,np.ones(3,bool))
    assert m['accuracy']==2/3 and m['balanced_accuracy']==.75 and m['top2']==1
    assert m['confusion']==[[1,0],[1,1]]
    assert probability_metrics(p,y,np.zeros(3,bool))['accuracy'] is None
