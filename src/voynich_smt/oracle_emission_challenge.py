"""Development-only diagnostics of unlabeled EM from supervised emissions."""
import numpy as np
from scipy.special import logsumexp
from voynich_smt.latent_cipher_classes import forward_backward,word_counts,prior_data,update,log_prior


def decomposition(chain,emissions,sequences):
    """Independent log-space posterior expectations; LL = E log joint + H."""
    a=np.log(chain['start']);t=np.log(chain['transition']);z=np.log(chain['stop']);e=np.log(emissions)
    result=dict(start=0.,transition=0.,stop=0.,emission=0.,posterior_entropy=0.,log_likelihood=0.)
    for seq in sequences:
        evidence=e[:,seq].T;n=len(seq);f=np.zeros_like(evidence);b=np.zeros_like(evidence);f[0]=a+evidence[0];b[-1]=z
        for i in range(1,n):f[i]=logsumexp(f[i-1,:,None]+t,axis=0)+evidence[i]
        ll=float(logsumexp(f[-1]+z))
        for i in range(n-2,-1,-1):b[i]=logsumexp(t+evidence[i+1,None,:]+b[i+1,None,:],axis=1)
        gamma=np.exp(f+b-ll)
        parts=dict(start=float(gamma[0]@a),stop=float(gamma[-1]@z),emission=float(np.sum(gamma*evidence)),transition=0.)
        for i in range(n-1):
            xi=np.exp(f[i,:,None]+t+evidence[i+1,None,:]+b[i+1,None,:]-ll)
            parts['transition']+=float(np.sum(xi*t))
        for key,value in parts.items():result[key]+=value
        result['posterior_entropy']+=ll-sum(parts.values());result['log_likelihood']+=ll
    return result


def snapshot(chain,emissions,sequences,endings,sharing):
    q,qe,within=prior_data(sequences,endings);r=decomposition(chain,emissions,sequences)
    r['prior']=log_prior(emissions,endings,q,qe,within,sharing);r['objective']=r['log_likelihood']+r['prior']
    return r


def em_step(chain,emissions,sequences,endings,sharing):
    ll,gamma=forward_backward(chain,emissions,sequences);q,qe,within=prior_data(sequences,endings)
    counts=word_counts(sequences,gamma,len(endings),chain['k'])
    return update(counts,endings,q,qe,within,sharing)


def changed_tokens(before,after,truth,sequences,offset=0):
    rows=[]
    for i,(a,b,y,seq) in enumerate(zip(before,after,truth,sequences)):
        pa=np.argmax(a,axis=1);pb=np.argmax(b,axis=1)
        for j in np.flatnonzero(pa!=pb):
            rows.append(dict(sentence_index=i,query=i>=offset,position=int(j),word_id=seq[j],gold=y[j],before=int(pa[j]),after=int(pb[j]),
                lost=bool(pa[j]==y[j] and pb[j]!=y[j]),gained=bool(pa[j]!=y[j] and pb[j]==y[j]),before_posterior=a[j].tolist(),after_posterior=b[j].tolist()))
    return rows
