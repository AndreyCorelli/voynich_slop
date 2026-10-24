"""Nested false-positive support masks; reference-supported classes retained."""
import numpy as np


def support_schedule(reference,seed):
    mask=np.asarray(reference,dtype=bool);rng=np.random.default_rng(seed);order=rng.permutation(mask.shape[1]);extra=[]
    for w in range(mask.shape[1]):
        options=np.flatnonzero(~mask[:,w])
        if not len(options):raise ValueError('Each word needs a forbidden candidate to perturb')
        extra.append(int(rng.choice(options)))
    return dict(order=order.tolist(),extra=extra,seed=seed)


def noisy_support(reference,schedule,rate):
    if not 0<=rate<=1:raise ValueError('rate must be in [0,1]')
    mask=np.asarray(reference,dtype=bool).copy();n=int(np.floor(rate*mask.shape[1]));affected=np.zeros(mask.shape[1],dtype=bool)
    for w in schedule['order'][:n]:mask[schedule['extra'][w],w]=True;affected[w]=True
    return mask,affected


def subset_score(probabilities,truth,sequences,type_mask):
    total=correct=0;gold_counts=np.zeros(probabilities[0].shape[1]);hits=np.zeros_like(gold_counts)
    for p,y,seq in zip(probabilities,truth,sequences):
        chosen=np.asarray(type_mask)[seq];gold=np.asarray(y)[chosen];pred=p.argmax(axis=1)[chosen]
        total+=len(gold);correct+=int((pred==gold).sum())
        np.add.at(gold_counts,gold,1);np.add.at(hits,gold,pred==gold)
    present=gold_counts>0
    return dict(tokens=total,correct=correct,accuracy=correct/total if total else None,
        balanced_accuracy=float(np.mean(hits[present]/gold_counts[present])) if total else None)
