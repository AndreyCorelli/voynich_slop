"""Public anchor/opaque inputs and context-only grammatical classifiers."""
from collections import Counter,defaultdict
import hashlib
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax
from scipy.sparse import csr_matrix,hstack
from voynich_smt.government_context import features as government_features
from voynich_smt.coarse_government import vocabulary,objective
from voynich_smt.dependency_role_proxy import encode
FUNCTIONS=frozenset({'ADP','CCONJ','SCONJ','PRON','DET','PART'})

def anchor_inventory(sentences):
    counts=defaultdict(Counter)
    for s in sentences:
        for t in s['tokens']:counts[t['word']][t['pos']]+=1
    result={}
    for w,c in counts.items():
        p=max(c,key=lambda p:(c[p],p))
        if sum(c.values())>=5 and p in FUNCTIONS:result[w]=p
    return result

def public_sentences(sentences,anchors,salt):
    return [dict(sent_id=s['sent_id'],tokens=[dict(id=hashlib.sha256((salt+'|'+t['word']).encode()).hexdigest(),anchor=t['word'] if t['word'] in anchors else None,tag=anchors.get(t['word'],'X')) for t in s['tokens']]) for s in sentences]

def public_features(public):
    result=[]
    for s in public:
        ts=s['tokens'];words=[t['anchor'] or 'OPAQUE' for t in ts];pos=[t['tag'] for t in ts]
        for i,t in enumerate(ts):
            f=government_features(words,pos,[0.]*len(ts),i,True)+['centerAnchorTag:'+t['tag']]
            if t['anchor'] is not None:f.append('centerAnchor:'+t['anchor'])
            for d in (-4,-3,-2,-1,1,2,3,4):
                j=i+d
                if 0<=j<len(ts) and ts[j]['anchor'] is not None:f.append('anchor'+str(d)+':'+ts[j]['anchor'])
            result.append(dict(sid=s['sent_id'],index=i,word=t['id'],anchor_tag=t['tag'],features=f))
    return result

def matrix(rows,v,soft=None):
    x=encode(rows,v)
    return x if soft is None else hstack([x,csr_matrix(soft)],format='csr')

def fit(rows,y,classes,soft=None):
    v=vocabulary(rows);x=matrix(rows,v,soft);y=np.asarray(y,int);k=len(classes);r=minimize(objective,np.zeros(x.shape[1]*k),args=(x,y,k),jac=True,method='L-BFGS-B',options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(vocabulary=v,classes=classes,weights=r.x.reshape(x.shape[1],k).tolist(),loss=float(r.fun),iterations=int(r.nit),n=len(y))

def predict(rows,model,soft=None):return softmax(matrix(rows,model['vocabulary'],soft)@np.array(model['weights']),axis=1)

def anchor_override(rows,q,classes):
    q=np.array(q,copy=True);index={p:i for i,p in enumerate(classes)}
    for i,r in enumerate(rows):
        if r['anchor_tag']!='X':q[i]=0.;q[i,index[r['anchor_tag']]]=1.
    return q

def pool(rows,q):
    groups=defaultdict(list)
    for i,r in enumerate(rows):groups[r['word']].append(i)
    result=np.array(q,copy=True)
    for ids in groups.values():result[ids]=np.mean(np.array(q)[ids],axis=0)
    return result
