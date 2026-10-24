"""POS-only probability that a nominal is a conjunct, as soft subject evidence."""
from collections import Counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from voynich_smt.dependency_role_proxy import encode,features as context_features

MODES=('pos','context')
WEIGHTS=(0.,.5,1.,2.,4.,8.)
NOMINAL=frozenset(('NOUN','PROPN','PRON'))


def features(tokens,index,mode):
    if mode not in MODES:raise ValueError(mode)
    pos=tokens[index]['pos'];row=['bias','pos:'+pos]
    if mode=='pos':return row
    row+=context_features(tokens,index,'pos')
    for direction,label in ((-1,'left'),(1,'right')):
        seq=range(index+direction,-1,-1) if direction<0 else range(index+1,len(tokens))
        marker=None;nominal=None
        for j in seq:
            if marker is None and tokens[j]['pos']=='CCONJ':marker=j
            if nominal is None and tokens[j]['pos'] in NOMINAL:nominal=j
            if marker is not None and nominal is not None:break
        distance=abs(index-marker) if marker is not None else 1000000;bucket=next((str(d) for d in (1,2,4,8) if distance<=d),'far');row.append(label+'-CCONJ:'+bucket)
        if nominal is None:row.append(label+'-nominal:BOUNDARY')
        else:
            lo,hi=sorted((index,nominal));between=any(t['pos']=='CCONJ' for t in tokens[lo+1:hi]);row.extend((label+'-nominal:'+tokens[nominal]['pos'],label+'-nominal-marker:'+str(between),label+'-nominal-pair:'+pos+'|'+tokens[nominal]['pos']+'|'+str(between)))
    return row


def objective(w,x,y,regularization=.001):
    scores=x@w;loss=float(np.mean(np.logaddexp(0.,scores)-y*scores))+.5*regularization*float(w@w);gradient=np.asarray(x.T@(expit(scores)-y)).ravel()/len(y)+regularization*w
    return loss,gradient


def fit(sentences,mode):
    rows=[];targets=[];counts=Counter()
    for tokens in sentences:
        for i,t in enumerate(tokens):
            if t['pos'] not in NOMINAL:continue
            row=features(tokens,i,mode);rows.append(row);counts.update(set(row));targets.append(int(t['rel'].split(':')[0]=='conj'))
    vocabulary={k:j for j,k in enumerate(sorted(k for k,n in counts.items() if n>=3))};x=encode(rows,vocabulary);y=np.asarray(targets);result=minimize(objective,np.zeros(len(vocabulary)),args=(x,y),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-10,gtol=1e-6));assert result.success,result.message
    return dict(mode=mode,vocabulary=vocabulary,weights=result.x.tolist(),training_nominals=len(y),conj_labels=int(y.sum()),regularization=.001,minimum_feature_count=3,loss=float(result.fun),iterations=int(result.nit))


def probabilities(tokens,subjects,model):
    x=encode([features(tokens,s,model['mode']) for s in subjects],model['vocabulary']);return expit(x@np.asarray(model['weights']))


def adjust(frames,tokens,model,weight):
    if weight<0:raise ValueError('Evidence weight must be nonnegative')
    if weight==0:return [dict(r) for r in frames]
    p=probabilities(tokens,[r['subject'] for r in frames],model);result=[]
    for r,q in zip(frames,p):
        other=dict(r);penalty=weight*float(np.log(max(1e-6,1-float(q))));other['scores']=[score+penalty for score in r['scores']];result.append(other)
    return result
