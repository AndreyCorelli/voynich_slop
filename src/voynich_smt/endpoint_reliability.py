"""Type-level, identity-free summaries and a veto on a frozen pair proposal."""
import math
import numpy as np


def profile(probabilities, sentences):
    q=np.asarray(probabilities,float)
    if not len(q):raise ValueError('empty profile')
    p=float(q.mean());eps=1e-12
    return [math.log((p+eps)/(1-p+eps)),float(q.var()),float((q>.5).mean()),
            float(-(q*np.log(q+eps)+(1-q)*np.log(1-q+eps)).mean()),
            math.log1p(len(q)),math.log1p(sentences)]


def pair_margin(pair, proposed, probabilities):
    if pair is None or any(i not in probabilities for i in pair):return None
    return min(math.log((probabilities[i]+1e-12)/(1-probabilities[i]+1e-12))*(1 if proposed[i]=='ADP' else -1) for i in pair)


def veto(pair, margin, cutoff):
    return pair if pair is not None and margin is not None and cutoff is not None and margin>=cutoff else None
