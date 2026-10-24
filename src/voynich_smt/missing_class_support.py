"""True-candidate deletion diagnostics with nonempty false-candidate fallback."""
import numpy as np
from voynich_smt.noisy_class_support import noisy_support


def deletion_schedule(reference,seed):
    reference=np.asarray(reference,dtype=bool);rng=np.random.default_rng(seed)
    return [int(rng.choice(np.flatnonzero(reference[:,w]))) for w in range(reference.shape[1])]


def missing_support(reference,addition_schedule,removed,rate):
    if not 0<=rate<=1:raise ValueError('rate must be in [0,1]')
    support,_=noisy_support(reference,addition_schedule,1.);affected=np.zeros(support.shape[1],bool)
    for w in addition_schedule['order'][:int(np.floor(rate*support.shape[1]))]:
        if not reference[removed[w],w]:raise ValueError('Deletion must remove a reference-supported class')
        support[removed[w],w]=False;affected[w]=True
    if not support.any(axis=0).all():raise ValueError('Empty candidate inventory')
    return support,affected


def cohorts(sequences,truth,support,affected,reference,offset):
    ids=np.concatenate(sequences);y=np.concatenate(truth);covered=support[y,ids];neighbors=[]
    for seq,gold in zip(sequences,truth):
        excluded=~support[np.asarray(gold),seq];adjacent=np.zeros(len(seq),bool)
        adjacent[1:]|=excluded[:-1];adjacent[:-1]|=excluded[1:];neighbors.extend(adjacent)
    masks=dict(all=np.ones(len(ids),bool),covered=covered,excluded=~covered,untouched=~affected[ids],
        covered_affected=covered&affected[ids],covered_neighbors=covered&np.asarray(neighbors),ambiguous_covered=covered&(reference.sum(axis=0)[ids]>1))
    query=np.arange(len(ids))>=sum(map(len,sequences[:offset]))
    masks.update({k+'_query':v&query for k,v in list(masks.items())})
    return y,masks


def token_metrics(prediction,gold,masks):
    out={}
    for name,mask in masks.items():
        y=gold[mask];pred=np.asarray(prediction)[mask];n=len(y);counts=np.bincount(y,minlength=8);hits=np.bincount(y[pred==y],minlength=8);present=counts>0
        out[name]=dict(tokens=n,correct=int((pred==y).sum()),accuracy=float((pred==y).mean()) if n else None,
            balanced_accuracy=float(np.mean(hits[present]/counts[present])) if n else None)
    return out
