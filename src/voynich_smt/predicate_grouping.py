"""Token-only predicate compatibility and arbitrary-count contiguous grouping."""
from copy import deepcopy
import math
import numpy as np

KINDS=('coordination','subordination','relative')


def pair_features(tokens,predicates,morph,attachments,first,second,rich=True):
    """Symmetric pair features; annotation labels/boundaries are not accepted."""
    if first==second or first not in predicates or second not in predicates:
        raise ValueError('Two distinct selected predicates required')
    left,right=sorted((first,second));between_count=sum(left<p<right for p in predicates)
    features=[math.log1p(right-left),math.log1p(between_count)]
    if not rich:return features
    width=len(morph[0]);local=[]
    for p in [left,right]:
        for delta in [-1,0,1]:
            i=p+delta;local+=morph[i] if 0<=i<len(tokens) else [0.]*width
    gap=np.asarray(morph[left+1:right],dtype=float)
    summaries=gap.mean(axis=0).tolist()+gap.max(axis=0).tolist() if len(gap) else [0.]*(2*width)
    flags=[]
    for p in [left,right]:
        own=[m for m in attachments if m['target']==p]
        flags += [float(any(k in m['kinds'] for m in own)) for k in KINDS]
        flags += [float(any(left<m['position']<right and k in m['kinds'] for m in own)) for k in KINDS]
    flags += [float(any(left<m['position']<right and m['target'] not in (None,left,right) and k in m['kinds'] for m in attachments)) for k in KINDS]
    return features+local+summaries+flags


def predict_pairs(tokens,predicates,adapter,attachments,model,rich=True):
    from .predicate_structure import morph_features
    morph=[morph_features(adapter.analyze(w)) for w in tokens]
    pairs=[(a,b) for i,a in enumerate(predicates) for b in predicates[i+1:]]
    rows=[pair_features(tokens,predicates,morph,attachments,a,b,rich) for a,b in pairs]
    probabilities=model.probability(rows) if rows else []
    return {f'{a}:{b}':float(p) for (a,b),p in zip(pairs,probabilities)}


def pair_probability(probabilities,a,b):
    if a==b:return 1.
    a,b=sorted((a,b));return probabilities[f'{a}:{b}']


def contiguous_groups(predicates,probabilities):
    """Exact DP over all contiguous partitions, with no fixed block count.

    Maximize within-block log odds; all between-block log(1-p) terms are a
    partition-invariant constant. Empty groups and gapless token boundaries
    are neither required nor inferred. Ties favor shorter final blocks.
    """
    n=len(predicates);block=np.zeros((n,n))
    for left in range(n):
        for right in range(left+1,n):
            p=min(1-1e-12,max(1e-12,pair_probability(probabilities,predicates[left],predicates[right])))
            block[left,right]=math.log(p/(1-p))
    interval=np.zeros((n,n))
    for left in range(n-1,-1,-1):
        for right in range(left+1,n):interval[left,right]=interval[left,right-1]+sum(block[i,right] for i in range(left,right))
    best=[0.]+[-math.inf]*n;cuts=[None]*(n+1)
    for end in range(1,n+1):
        for start in range(end-1,-1,-1):
            value=best[start]+interval[start,end-1]
            if value>best[end]+1e-12:best[end]=value;cuts[end]=start
    groups=[];end=n
    while end:
        start=cuts[end];groups.append(predicates[start:end]);end=start
    return list(reversed(groups)),float(best[n])


def restrict_or_rescore(prediction,probabilities,mode):
    """Apply fixed compatibility decisions without reference annotations."""
    if mode not in ['soft','pair_filter','partition']:raise ValueError('Unknown grouping mode')
    result=deepcopy(prediction);groups=None;partition_score=None
    if mode=='partition':
        groups,partition_score=contiguous_groups(prediction['predicates'],probabilities)
        membership={p:i for i,g in enumerate(groups) for p in g}
    options={}
    for c,rows in prediction['arc_candidates'].items():
        child=int(c);retained=[]
        for r in rows:
            parent=r['parent'];penalty=0.
            if parent is not None:
                p=pair_probability(probabilities,child,parent)
                if mode=='pair_filter' and p<.5:continue
                if mode=='partition' and membership[child]!=membership[parent]:continue
                if mode=='soft':penalty=math.log(max(1e-12,p))
            candidate=deepcopy(r);candidate['parent_logit']=r['logit'];candidate['grouping_log_probability']=penalty
            candidate['logit']=r['logit']+penalty;retained.append(candidate)
        normalizer=float(np.logaddexp.reduce([r['logit'] for r in retained]))
        for r in retained:r['conditional_probability']=float(math.exp(r['logit']-normalizer))
        options[child]=retained
    result['arc_candidates']=options
    return result,{'mode':mode,'predicate_groups':groups,'partition_score':partition_score}
