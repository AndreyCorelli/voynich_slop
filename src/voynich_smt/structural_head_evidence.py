"""Learn phrase eligibility and head/carrier clause compatibility from POS context."""
from collections import Counter
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from voynich_smt.copular_head_oracle import flags
from voynich_smt.dependency_role_proxy import encode
from voynich_smt.typed_predicate_units import select

TASKS=('phrase','clause')
MODES=('coarse','context')
WEIGHTS=(0.,.5,1.,2.,4.)
ARMS=('phrase','clause','joint')


def features(tokens,head,carrier,mode):
    if mode not in MODES:raise ValueError(mode)
    hp=tokens[head]['pos'];vp=tokens[carrier]['pos'];distance=abs(head-carrier)
    bucket=next((str(b) for b in (0,1,2,4,8,16,32) if distance<=b),'far')
    result=['bias','head:'+hp,'carrier:'+vp,'hp-vp:'+hp+'|'+vp,'distance:'+bucket,'order:'+str(np.sign(head-carrier)),'hp-distance:'+hp+'|'+bucket]
    if mode=='context':
        for name,index in (('h',head),('v',carrier)):
            window=[]
            for offset in range(-2,3):
                j=index+offset;p=tokens[j]['pos'] if 0<=j<len(tokens) else 'BOUNDARY';window.append(p);result.append(f'{name}{offset}:{p}')
            result.extend((name+'-prev:'+window[1]+'|'+window[2],name+'-next:'+window[2]+'|'+window[3],name+'-flank:'+window[1]+'|'+window[3]))
        lo,hi=sorted((head,carrier));between=Counter(t['pos'] for t in tokens[lo+1:hi])
        for p in ('VERB','AUX','SCONJ','CCONJ','ADP','NOUN','ADJ','PRON'):
            result.append('between-'+p+':'+str(min(between[p],3)))
        result.append('head-carrier-prev:'+hp+'|'+(tokens[carrier-1]['pos'] if carrier else 'BOUNDARY'))
    return result


def objective(flat,x,y,frame_weights,regularization=.001):
    w=flat.reshape(x.shape[1],2);scores=x@w;scale=frame_weights/frame_weights.sum()/2
    loss=float(np.sum(scale[:,None]*(np.logaddexp(0.,scores)-y*scores)))+.5*regularization*float(flat@flat)
    gradient=x.T@((expit(scores)-y)*scale[:,None])+regularization*w
    return loss,np.asarray(gradient).ravel()


def fit(frames,data,mode):
    rows=[];targets=[];weights=[];counts=Counter()
    for frame in frames:
        tokens=data[frame['sid']]['tokens'];carrier=frame['gold'][2];heads=sorted({h for h,_ in frame['options']})
        for head in heads:
            row=features(tokens,head,carrier,mode);rows.append(row);counts.update(set(row));f=flags(tokens,head,carrier);targets.append([int(f[t]) for t in TASKS]);weights.append(1/len(heads))
    vocabulary={k:i for i,k in enumerate(sorted(k for k,n in counts.items() if n>=3))};x=encode(rows,vocabulary);y=np.asarray(targets);weights=np.asarray(weights)
    result=minimize(objective,np.zeros(len(vocabulary)*2),args=(x,y,weights),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-10,gtol=1e-6));assert result.success,result.message
    return dict(mode=mode,vocabulary=vocabulary,weights=result.x.reshape(len(vocabulary),2).tolist(),training_frames=len(frames),training_pairs=len(rows),weighted_positive_rates=(weights@y/weights.sum()).tolist(),regularization=.001,minimum_feature_count=3,iterations=int(result.nit),loss=float(result.fun))


def probabilities(tokens,carrier,heads,model):
    x=encode([features(tokens,h,carrier,model['mode']) for h in heads],model['vocabulary']);p=expit(x@np.asarray(model['weights']))
    # A token shares a clause with itself independently of any annotation.
    for j,h in enumerate(heads):
        if h==carrier:p[j,1]=1.
    return p


def evidence(tokens,carrier,options,model):
    heads=sorted({h for h,_ in options});p=probabilities(tokens,carrier,heads,model);lookup={h:p[j] for j,h in enumerate(heads)}
    return np.asarray([np.log(np.maximum(1e-6,lookup[h])) for h,_ in options])


def infer(scores,options,subject,carrier,cues,phrase_weight,clause_weight):
    return select(scores+cues@np.asarray([phrase_weight,clause_weight]),options,subject,carrier)


def calibrate(frames,arm):
    if arm not in ARMS:raise ValueError(arm)
    grid=[(p,c) for p in WEIGHTS for c in WEIGHTS if (arm!='phrase' or c==0) and (arm!='clause' or p==0)];records=[]
    for p,c in grid:
        correct=sum(infer(r['scores'],r['options'],r['gold'][0],r['gold'][2],r['cues'],p,c)==r['gold'] for r in frames)
        records.append(dict(phrase_weight=p,clause_weight=c,correct=correct,n=len(frames)))
    return dict(selected=max(records,key=lambda r:(r['correct'],-r['phrase_weight']-r['clause_weight'],-r['clause_weight'],-r['phrase_weight'])),grid=records)
