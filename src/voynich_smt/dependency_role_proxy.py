"""Source-only token role probabilities and soft additions to frozen unit scores."""
from collections import Counter,defaultdict
import math
import numpy as np
from scipy.sparse import csr_matrix
from scipy.optimize import minimize
from voynich_smt.copular_head_oracle import DEPENDENTS
from voynich_smt.typed_predicate_units import select

CLASSES=('dependent','cop','aux','other')
WEIGHTS=(0.,.5,1.,2.,4.)
MODES=('pos','lexical')
ARMS=('head','type','joint')


def label(token):
    rel=token['rel'].split(':')[0]
    return 'dependent' if rel in DEPENDENTS else rel if rel in ('cop','aux') else 'other'


def features(tokens,index,mode):
    if mode not in MODES:raise ValueError(mode)
    result=['bias'];pos=[]
    for offset in range(-2,3):
        j=index+offset;p=tokens[j]['pos'] if 0<=j<len(tokens) else 'BOUNDARY';pos.append(p);result.append(f'p{offset}:{p}')
    result.extend(('pprev:'+pos[1]+'|'+pos[2],'pnext:'+pos[2]+'|'+pos[3],'pflank:'+pos[1]+'|'+pos[3]))
    if mode=='lexical':
        for offset in (-1,0,1):
            j=index+offset
            if 0<=j<len(tokens):result.append(f'w{offset}:'+tokens[j]['word'])
        word=tokens[index]['word']
        for length in (2,3,4):
            if len(word)>=length:result.append(f's{length}:'+word[-length:]+'|'+tokens[index]['pos'])
    return result


def encode(feature_rows,vocabulary):
    data=[];columns=[];starts=[0]
    for row in feature_rows:
        for feature in set(row):
            if feature in vocabulary:columns.append(vocabulary[feature]);data.append(1.)
        starts.append(len(columns))
    return csr_matrix((data,columns,starts),shape=(len(feature_rows),len(vocabulary)))


def objective(flat,x,y,regularization=.001):
    weights=flat.reshape(x.shape[1],len(CLASSES));scores=x@weights;maximum=scores.max(axis=1);exp=np.exp(scores-maximum[:,None]);sums=exp.sum(axis=1);loss=np.mean(np.log(sums)+maximum-scores[np.arange(len(y)),y])+.5*regularization*float(flat@flat)
    residual=exp/sums[:,None];residual[np.arange(len(y)),y]-=1;gradient=x.T@residual/len(y)+regularization*weights
    return float(loss),np.asarray(gradient).ravel()


def fit(sentences,mode):
    rows=[];targets=[];counts=Counter();pos_counts=defaultdict(Counter)
    for tokens in sentences:
        for i,t in enumerate(tokens):
            row=features(tokens,i,mode);rows.append(row);counts.update(row);y=label(t);targets.append(CLASSES.index(y));pos_counts[t['pos']][y]+=1
    vocabulary={feature:i for i,feature in enumerate(sorted(k for k,n in counts.items() if n>=3))};x=encode(rows,vocabulary);y=np.asarray(targets);result=minimize(objective,np.zeros(len(vocabulary)*len(CLASSES)),args=(x,y),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-10,gtol=1e-6));assert result.success,result.message
    return dict(mode=mode,vocabulary=vocabulary,weights=result.x.reshape(len(vocabulary),len(CLASSES)).tolist(),pos_counts={k:dict(v) for k,v in pos_counts.items()},training_tokens=len(y),class_counts={c:int(np.sum(y==j)) for j,c in enumerate(CLASSES)},regularization=.001,minimum_feature_count=3,loss=float(result.fun),iterations=int(result.nit))


def probabilities(tokens,model):
    x=encode([features(tokens,i,model['mode']) for i in range(len(tokens))],model['vocabulary']);scores=x@np.asarray(model['weights']);scores-=scores.max(axis=1,keepdims=True);mass=np.exp(scores);return mass/mass.sum(axis=1,keepdims=True)


def pos_prior(model,pos):
    counts=model['pos_counts'].get(pos,{});n=sum(counts.values());return np.asarray([(counts.get(c,0)+.5)/(n+.5*len(CLASSES)) for c in CLASSES])


def evidence(tokens,carrier,options,probabilities_by_token,model):
    # Ratios discount the role frequency already predictable from POS.
    head=[];type_score=[];carrier_prior=pos_prior(model,tokens[carrier]['pos'])
    for h,role in options:
        prior=pos_prior(model,tokens[h]['pos']);head.append(math.log(max(1e-6,1-probabilities_by_token[h,0]))-math.log(max(1e-6,1-prior[0])))
        j=CLASSES.index('other' if role=='direct' else role);type_score.append(math.log(max(1e-6,probabilities_by_token[carrier,j]))-math.log(max(1e-6,carrier_prior[j])))
    return np.asarray(head),np.asarray(type_score)


def infer(scores,options,subject,carrier,head,type_score,head_weight,type_weight):
    return select(scores+head_weight*head+type_weight*type_score,options,subject,carrier)


def calibrate(frames,arm):
    if arm not in ARMS:raise ValueError(arm)
    grid=[(h,t) for h in WEIGHTS for t in WEIGHTS if (arm!='head' or t==0) and (arm!='type' or h==0)];records=[]
    for h,t in grid:
        correct=sum(infer(r['scores'],r['options'],r['gold'][0],r['gold'][2],r['head'],r['type'],h,t)==r['gold'] for r in frames);records.append(dict(head_weight=h,type_weight=t,correct=correct,n=len(frames)))
    chosen=max(records,key=lambda r:(r['correct'],-r['head_weight']-r['type_weight'],-r['type_weight'],-r['head_weight']))
    return dict(selected=chosen,grid=records)
