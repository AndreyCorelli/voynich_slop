"""Replace a local POS marginal while preserving token-specific grammar."""
from collections import defaultdict
import numpy as np

def pos_mass(labels,p):
    out=defaultdict(float)
    for (_,g),q in zip(labels,p):out[g[0]]+=q
    return dict(out)

def replace_pos(labels,p,new_mass):
    old=pos_mass(labels,p)
    return np.array([q*new_mass.get(g[0],0)/old[g[0]] if old[g[0]] else 0. for (_,g),q in zip(labels,p)])

def pooled_marginal(marginals,indices,current=None):
    selected=[i for i in indices if i!=current]
    if not selected:return None
    keys=set().union(*(marginals[i] for i in selected))
    return {k:sum(marginals[i].get(k,0) for i in selected)/len(selected) for k in keys}

def task_scores(labels,p):
    return dict(subject=float(sum(q for (role,_),q in zip(labels,p) if role=='nsubj')),nominative=float(sum(q for (_,g),q in zip(labels,p) if g[0] in ('NOUN','ADJ') and g[1]=='Nom')))

def counts(rows,task,arm,threshold):
    tp=fp=fn=tn=0
    for r in rows:
        gold=r['labels'][task];pred=r['scores'][arm][task]>=threshold
        tp+=gold and pred;fp+=not gold and pred;fn+=gold and not pred;tn+=not gold and not pred
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else 0.,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.,predicted=tp+fp,n=len(rows))

def select_policy(rows,task,arm):
    candidates=[]
    for i in range(101):
        t=i/100;c=counts(rows,task,arm,t);types=len({r['word'] for r in rows if r['scores'][arm][task]>=t});candidates.append((t,c,types))
    best=max(candidates,key=lambda x:(x[1]['f1'],x[0]));eligible=[r for r in candidates if r[1]['precision'] is not None and r[1]['precision']>=.9 and r[1]['predicted']>=20 and r[2]>=10]
    high=max(eligible,key=lambda x:(x[1]['tp'],x[1]['precision'],x[0])) if eligible else None
    return dict(f1=dict(threshold=best[0],calibration=best[1]),precision90=dict(threshold=high[0],calibration=high[1],types=high[2]) if high else None)
