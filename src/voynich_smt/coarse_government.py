"""Joint PP/head-category probes and probability-valued downstream features."""
from collections import Counter
import hashlib
import numpy as np
from scipy.sparse import csr_matrix,hstack
from scipy.optimize import minimize
from scipy.special import softmax,expit
from voynich_smt.dependency_role_proxy import encode
from voynich_smt.contextual_nominative import objective as binary_objective
HEADS=('VERBAL','NOMINAL','OTHER','ROOT')
CLASSES=tuple((pp,h) for pp in (False,True) for h in HEADS)

def fold(sid):return int(hashlib.sha256(str(sid).encode()).hexdigest()[:8],16)%3

def structure_label(row):
    pp='oraclePP:present=True' in row['pp_bundle'];head='ROOT'
    for f in row['structure_bundle']:
        if f.startswith('oracleHead:pos='):
            p=f.split('=',1)[1];head='VERBAL' if p in ('VERB','AUX') else 'NOMINAL' if p in ('NOUN','PROPN','ADJ','PRON') else 'OTHER'
    return CLASSES.index((pp,head))

def vocabulary(rows):
    c=Counter(f for row in rows for f in set(row));return {f:i for i,f in enumerate(sorted(f for f,n in c.items() if n>=3))}

def objective(w,x,y,k=8):
    weights=w.reshape(x.shape[1],k);scores=x@weights;mass=softmax(scores,axis=1);loss=-np.mean(np.log(np.maximum(1e-300,mass[np.arange(len(y)),y])))+.0005*(w@w);mass[np.arange(len(y)),y]-=1;gradient=np.asarray(x.T@mass/len(y))+.001*weights
    return float(loss),gradient.ravel()

def fit_probe(rows,y):
    v=vocabulary(rows);x=encode(rows,v);y=np.array(y,int);r=minimize(objective,np.zeros(x.shape[1]*8),args=(x,y),jac=True,method='L-BFGS-B',options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(vocabulary=v,weights=r.x.reshape(x.shape[1],8).tolist(),loss=float(r.fun),iterations=int(r.nit),n=len(y))

def probe(rows,model):return softmax(encode(rows,model['vocabulary'])@np.array(model['weights']),axis=1)

def case_matrix(rows,probs,v):return hstack([encode(rows,v),csr_matrix(probs)],format='csr')

def fit_case(rows,probs,y):
    v=vocabulary(rows);x=case_matrix(rows,probs,v);y=np.asarray(y,float);r=minimize(binary_objective,np.zeros(x.shape[1]),args=(x,y),jac=True,method='L-BFGS-B',options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(vocabulary=v,weights=r.x.tolist(),loss=float(r.fun),iterations=int(r.nit),n=len(y))

def case_probability(rows,probs,model):return expit(case_matrix(rows,probs,model['vocabulary'])@np.array(model['weights']))

def sham(rows,probs,seed):
    rng=np.random.default_rng(seed);groups={}
    for i,r in enumerate(rows):groups.setdefault(r['sid'],[]).append(i)
    result=np.array(probs,copy=True)
    for ids in groups.values():result[ids]=np.array(probs)[rng.permutation(ids)]
    return result
