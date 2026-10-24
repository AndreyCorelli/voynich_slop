"""Capped word-level candidate proposals from flagged cavity predictions."""
import numpy as np


def propose(support,word_ids,context,flagged,k=2,strategy='context',seed=0):
    support=np.asarray(support,dtype=bool);ids=np.asarray(word_ids);context=np.asarray(context);flagged=np.asarray(flagged,dtype=bool)
    if k<1 or strategy not in ('context','random'):raise ValueError('Positive cap and known strategy required')
    rng=np.random.default_rng(seed);additions={}
    for w in np.unique(ids[flagged]):
        outside=np.flatnonzero(~support[:,w]);selected=flagged&(ids==w)
        if not len(outside):continue
        if strategy=='context':
            p=context[selected][:,outside];mass=p.sum(axis=1,keepdims=True)
            p=np.divide(p,mass,out=np.full_like(p,1/len(outside)),where=mass>0);average=p.mean(axis=0)
            ordered=outside[np.argsort(-average,kind='stable')]
        else:ordered=rng.permutation(outside)
        additions[str(int(w))]=ordered[:min(k,len(outside))].tolist()
    return additions


def expand(support,additions):
    result=np.asarray(support,dtype=bool).copy()
    for w,classes in additions.items():result[np.asarray(classes,dtype=int),int(w)]=True
    return result
