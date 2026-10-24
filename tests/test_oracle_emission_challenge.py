import itertools
import numpy as np
from voynich_smt.latent_cipher_classes import fixed_chain,forward_backward
from voynich_smt.oracle_emission_challenge import decomposition,em_step,changed_tokens


def test_decomposition_against_enumerated_paths():
    chain=fixed_chain([[0,1,0],[1,0],[1]],2);em=np.array([[.75,.25],[.3,.7]]);seqs=[[1],[0,1,0]]
    result=decomposition(chain,em,seqs);expected={k:0. for k in result}
    for seq in seqs:
        paths=list(itertools.product(range(2),repeat=len(seq)));parts=[]
        for path in paths:
            parts.append(dict(start=np.log(chain['start'][path[0]]),stop=np.log(chain['stop'][path[-1]]),
                transition=sum(np.log(chain['transition'][a][b]) for a,b in zip(path,path[1:])),emission=sum(np.log(em[s,w]) for s,w in zip(path,seq))))
        weights=np.exp([sum(p.values()) for p in parts]);z=weights.sum();posterior=weights/z
        expected['log_likelihood']+=np.log(z);expected['posterior_entropy']-=sum(posterior*np.log(posterior))
        for p,weight in zip(parts,posterior):
            for k,v in p.items():expected[k]+=weight*v
    for k in expected:np.testing.assert_allclose(result[k],expected[k],atol=1e-12)
    np.testing.assert_allclose(result['log_likelihood'],forward_backward(chain,em,seqs)[0])


def test_em_identity_and_posterior_kl():
    chain=fixed_chain([[0,1,0],[1,0]],2);e=np.array([[.8,.2],[.4,.6]]);seqs=[[0,1,0],[1,1]];new=em_step(chain,e,seqs,[0,1],False)
    ll,gamma=forward_backward(chain,e,seqs);nl,_=forward_backward(chain,new,seqs)
    q=sum(float(p@np.log(new[:,w]/e[:,w])) for seq,g in zip(seqs,gamma) for w,p in zip(seq,g));kl=0.
    for seq in seqs:
        distributions=[]
        for em in (e,new):
            weights=[]
            for path in itertools.product(range(2),repeat=len(seq)):
                prob=chain['start'][path[0]]*chain['stop'][path[-1]]
                for i,(w,s) in enumerate(zip(seq,path)):
                    prob*=em[s,w]
                    if i:prob*=chain['transition'][path[i-1]][s]
                weights.append(prob)
            weights=np.array(weights);distributions.append(weights/weights.sum())
        a,b=distributions;kl+=sum(a*np.log(a/b))
    np.testing.assert_allclose(nl-ll,q+kl,atol=1e-12);assert kl>=0


def test_changes_distinguish_loss_gain_and_background():
    a=[np.array([[.9,.1],[.8,.2]])];b=[np.array([[.1,.9],[.1,.9]])]
    changes=changed_tokens(a,b,[[0,1]],[[4,5]],offset=1)
    assert [r['lost'] for r in changes]==[True,False]
    assert [r['gained'] for r in changes]==[False,True]
    assert not any(r['query'] for r in changes)
