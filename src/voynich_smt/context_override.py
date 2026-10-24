"""Label-free cavity/candidate signals and calibrated one-pass tag overrides."""
import numpy as np


def signals(context,ordinary,support,word_ids):
    context=np.asarray(context);ordinary=np.asarray(ordinary);ids=np.asarray(word_ids);support=np.asarray(support,dtype=bool)
    old=ordinary.argmax(axis=1);new=context.argmax(axis=1);rows=np.arange(len(ids))
    outside=~support[:,ids].T
    return dict(old=old.tolist(),new=new.tolist(),disagree=(old!=new).tolist(),outside_top=outside[rows,new].tolist(),
        confidence=context[rows,new].tolist(),ratio=(context[rows,new]/np.maximum(context[rows,old],1e-300)).tolist(),
        outside_mass=(context*outside).sum(axis=1).tolist(),conflict=(1.-np.sum(context*ordinary,axis=1)).tolist())


def choose(features,policy):
    if not policy['enabled']:return np.zeros(len(features['old']),bool)
    mask=np.asarray(features['disagree'])&(np.asarray(features['confidence'])>=policy['confidence'])&(np.asarray(features['ratio'])>=policy['ratio'])
    if policy['gate']=='outside':mask&=np.asarray(features['outside_top'])
    return mask


def apply(features,policy):
    mask=choose(features,policy);pred=np.asarray(features['old']).copy();pred[mask]=np.asarray(features['new'])[mask]
    return pred,mask


def counts(features,gold,selected,excluded):
    y=np.asarray(gold);a=np.asarray(features['old']);b=np.asarray(features['new']);selected=np.asarray(selected,dtype=bool);excluded=np.asarray(excluded,dtype=bool)
    corrected=selected&(a!=y)&(b==y);spoiled=selected&(a==y)&(b!=y);covered=~excluded
    return dict(tokens=len(y),overrides=int(selected.sum()),corrected=int(corrected.sum()),spoiled=int(spoiled.sum()),net_gain=int(corrected.sum()-spoiled.sum()),
        unchanged_wrong=int((selected&(a!=y)&(b!=y)).sum()),excluded=int(excluded.sum()),flagged_excluded=int((selected&excluded).sum()),recovered_excluded=int((corrected&excluded).sum()),
        correct_covered=int(((a==y)&covered).sum()),spoiled_correct_covered=int((spoiled&covered).sum()),baseline_correct=int((a==y).sum()))


def calibrate(records,grid,risk=.01,gate='outside'):
    best=dict(enabled=False,gate=gate,confidence=None,ratio=None);best_counts=None;best_key=(0,0,0,0.,0.)
    for confidence in grid['confidence']:
        for ratio in grid['ratio']:
            policy=dict(enabled=True,gate=gate,confidence=confidence,ratio=ratio);totals=None
            for r in records:
                c=counts(r['features'],r['gold'],choose(r['features'],policy),r['excluded'])
                totals=c if totals is None else {k:totals[k]+c[k] for k in c}
            if totals['net_gain']<=0 or totals['spoiled_correct_covered']>risk*totals['correct_covered']:continue
            key=(totals['net_gain'],-totals['spoiled'],-totals['overrides'],confidence,ratio)
            if key>best_key:best=policy;best_counts=totals;best_key=key
    if not best['enabled']:
        best_counts={}
        for r in records:
            c=counts(r['features'],r['gold'],np.zeros(len(r['gold']),bool),r['excluded'])
            for k,v in c.items():best_counts[k]=best_counts.get(k,0)+v
    return dict(policy=best,calibration=best_counts,risk_budget=risk)


def ranking(scores,positive):
    scores=np.asarray(scores);positive=np.asarray(positive,dtype=bool);n=int(positive.sum());neg=len(positive)-n
    if not n or not neg:return dict(positives=n,negatives=neg,auroc=None,average_precision=None)
    order=np.argsort(-scores,kind='stable');s=scores[order];p=positive[order];tp=fp=0;area=ap=0.
    for start in np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1]:
        end=int(np.searchsorted(-s,-s[start],side='right'));a=int(p[start:end].sum());b=end-int(start)-a
        area+=a*(neg-fp-b)+.5*a*b
        tp+=a;fp+=b;ap+=(a/n)*(tp/(tp+fp))
    return dict(positives=n,negatives=neg,auroc=area/(n*neg),average_precision=ap)
