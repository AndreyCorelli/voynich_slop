"""Direct context-only nominal-nominative probability, with soft role transfer."""
from collections import Counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from voynich_smt.dependency_role_proxy import encode

def features(pos,i):
    def at(d):return pos[i+d] if 0<=i+d<len(pos) else 'BOUNDARY'
    return ['bias']+[str(d)+':'+at(d) for d in (-2,-1,1,2)]+['flank:'+at(-1)+'|'+at(1)]

def objective(w,x,y,regularization=.001):
    z=x@w;p=expit(z)
    return float(np.mean(np.logaddexp(0,z)-y*z)+.5*regularization*(w@w)),np.asarray(x.T@(p-y)/len(y))+regularization*w

def fit(rows,y):
    counts=Counter(f for row in rows for f in set(row));v={f:i for i,f in enumerate(sorted(f for f,n in counts.items() if n>=3))};x=encode(rows,v);y=np.asarray(y,float)
    result=minimize(objective,np.zeros(len(v)),args=(x,y),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-11,gtol=1e-7));assert result.success,result.message
    return dict(vocabulary=v,weights=result.x.tolist(),regularization=.001,minimum_feature_count=3,loss=float(result.fun),iterations=int(result.nit),training_tokens=len(y),positives=int(sum(y)))

def probability(rows,model):return expit(encode(rows,model['vocabulary'])@np.array(model['weights']))

def nominal(g):return g[0] in ('NOUN','ADJ') and g[1]=='Nom'

def replace_nominal(labels,p,q):
    flags=np.array([nominal(g) for _,g in labels]);old=sum(v for v,f in zip(p,flags) if f)
    return np.array([v*q/old if f and old else v*(1-q)/(1-old) if not f and old<1 else 0. for v,f in zip(p,flags)])
