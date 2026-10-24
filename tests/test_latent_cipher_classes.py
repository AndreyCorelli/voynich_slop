import itertools
import copy
import numpy as np
from voynich_smt.latent_cipher_classes import fixed_chain,forward_backward,fit,prior_data,update,relation_edges
from benchmarks.grammar_latent_classes_iteration26 import observe,arm_input


def test_forward_backward_exhaustive_variable_lengths():
    chain=fixed_chain([[0,1,0],[1,1],[0]],2);em=np.array([[.7,.3],[.2,.8]])
    sequences=[[0],[1,0],[0,1,1,0]];ll,gamma=forward_backward(chain,em,sequences);expected=0
    for seq,g in zip(sequences,gamma):
        weights=[];paths=list(itertools.product(range(2),repeat=len(seq)))
        for path in paths:
            p=chain['start'][path[0]]*chain['stop'][path[-1]]
            for t,(w,state) in enumerate(zip(seq,path)):
                p*=em[state,w]
                if t:p*=chain['transition'][path[t-1]][state]
            weights.append(p)
        total=sum(weights);expected+=np.log(total);marginal=np.zeros_like(g)
        for path,p in zip(paths,weights):
            for t,state in enumerate(path):marginal[t,state]+=p/total
        np.testing.assert_allclose(g,marginal,atol=1e-12)
    np.testing.assert_allclose(ll,expected,atol=1e-12)


def test_em_monotonic_and_chain_immutable():
    chain=fixed_chain([[0,1,0],[1,0,1]],2);original=copy.deepcopy(chain);seq=[[0,1,0,2],[1,2],[0,2,1]];we=[0,1,0]
    for sharing in (False,True):
        model=fit(chain,seq,we,17,sharing,max_iter=30,tolerance=0)
        assert min(np.diff([t['objective'] for t in model['trace']]))>=-1e-8
        np.testing.assert_allclose(np.sum(model['emissions'],axis=1),1)
    assert chain==original


def test_factorized_emission_normalization():
    seq=[[0,1,2,3,0]];we=[0,0,1,1];q,qe,within=prior_data(seq,we)
    counts=np.array([[2.,0,1,0],[0,1,0,1]])
    for sharing in (False,True):
        em=update(counts,we,q,qe,within,sharing)
        assert np.all(em>0);np.testing.assert_allclose(em.sum(axis=1),1)


def test_rekey_and_metadata_invariance():
    rows=[dict(tokens=['puella','amat','puellam']),dict(tokens=['amat','puella','agrum'])]
    a=observe(rows);b=observe([dict(s,upos=['WRONG']*3,edges=[[0,1,1]]) for s in rows],26032)
    assert a==b
    chain=fixed_chain([[0,1,0],[1,0,0]],2)
    assert fit(chain,**dict(sequences=a['sequences'],word_endings=a['word_endings']),seed=17)==fit(chain,b['sequences'],b['word_endings'],17)


def test_control_counts():
    obs=dict(sequences=[[0,1,0],[2,3,1]],word_endings=[0,0,1,2])
    seq,we=arm_input(obs,'shuffled_context')
    assert [sorted(s) for s in seq]==[sorted(s) for s in obs['sequences']]
    seq,we=arm_input(obs,'shuffled_endings');assert sorted(we)==sorted(obs['word_endings']);assert seq==obs['sequences']


def test_cycles_removed_and_ties_abstain():
    table=np.zeros((12,2,2,5));table[:,:,:,1]=.8
    model=dict(probabilities=table.tolist(),radius=12)
    edges=relation_edges(np.eye(2),model,.5)
    assert len(edges)==1
    assert relation_edges(np.ones((3,2))*.5,model,.5)==[]
