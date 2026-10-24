"""One-parameter monotone offset fitted without repair outcomes."""
import numpy as np
from scipy.special import expit


def logits(probabilities):
    p=np.asarray(probabilities,float)
    return np.log((p+1e-12)/(1-p+1e-12))


def fit_offset(probabilities,labels,balanced=False):
    x=logits(probabilities);y=np.asarray(labels,float)
    if set(y)!={0.,1.}:raise ValueError('both classes required')
    w=np.ones(len(y))
    if balanced:
        for c in [0.,1.]:w[y==c]=1./np.count_nonzero(y==c)
    target=float(np.dot(w,y)/w.sum());lo,hi=-40.,40.
    for _ in range(160):
        mid=(lo+hi)/2
        if float(np.dot(w,expit(x+mid))/w.sum())<target:lo=mid
        else:hi=mid
    return dict(offset=(lo+hi)/2,balanced=balanced,n=len(y),target_mean=target)


def apply_offset(probabilities,model):
    return expit(logits(probabilities)+model['offset'])
