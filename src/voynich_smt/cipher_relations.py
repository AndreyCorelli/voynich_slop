"""Key-invariant, lexical-identity-free features for cipher relation diagnostics."""
from collections import Counter
from functools import lru_cache
import hashlib
import math
import random
import string
import numpy as np
from scipy.sparse import csr_matrix
from scipy.optimize import minimize
from scipy.special import logsumexp

ARMS=('geometry','repetition','ending_blind','ending_exposed','dictionary')
LABELS=('none','subject','object','nominal_modifier','coordination')
RADIUS=12
DIM=4096


def encrypt(sentences,seed):
    rng=random.Random(seed);alphabet=list(string.ascii_lowercase+'#');shuffled=alphabet[:];rng.shuffle(shuffled);sub=dict(zip(alphabet,shuffled))
    vocabulary=sorted({w for s in sentences for w in s['tokens']});mapping={};occupied=set()
    for w in vocabulary:
        while True:
            prefix=''.join(rng.choices(string.ascii_lowercase,k=10))
            if prefix not in occupied:occupied.add(prefix);break
        suffix=('#'+w)[-2:]
        mapping[w]=prefix+''.join(sub[c] for c in suffix)
    return [[mapping[w] for w in s['tokens']] for s in sentences],mapping


def stats(sequences,ending=False):
    flattened=[w[-2:] if ending else w for s in sequences for w in s]
    counts=Counter(flattened);first={}
    for i,w in enumerate(flattened):first.setdefault(w,i)
    ranks={w:i for i,w in enumerate(sorted(counts,key=lambda w:(-counts[w],first[w])))}
    return {'counts':counts,'ranks':ranks,'total':len(flattened)}


def views(sentences,seed,lattice):
    sequences,mapping=encrypt(sentences,seed);word_stats=stats(sequences);ending_stats=stats(sequences,True);result=[]
    for s,cipher in zip(sentences,sequences):
        metadata={}
        for word,code in zip(s['tokens'],cipher):
            readings=lattice.get(word,[])
            morph={}
            for reading in readings:
                morph.setdefault('pos',set()).add(reading['pos'])
                for key,val in reading['features']:
                    if key in ('Case','Number','Gender','Mood','Voice'):morph.setdefault(key,set()).add(val)
            metadata[code]={'exposed_suffix':('#'+word)[-2:],'morph':morph}
        result.append(dict(tokens=cipher,metadata=metadata,word_stats=word_stats,ending_stats=ending_stats))
    return result


def token_features(view,pos,arm,masked_type=None):
    if not 0<=pos<len(view['tokens']):return ['boundary']
    word=view['tokens'][pos]
    if word==masked_type:return ['masked']
    if arm=='geometry':return []
    result=[]
    def frequency(kind,key):
        st=view[kind+'_stats'];count=st['counts'][key];rank=st['ranks'][key]
        return [f'{kind}_count={min(12,int(math.log2(count)))}',f'{kind}_rank={min(24,rank)}']
    result+=frequency('word',word)
    if arm in ('ending_blind','ending_exposed','dictionary'):result+=frequency('ending',word[-2:])
    if arm=='ending_exposed':result.append('latin_ending='+view['metadata'][word]['exposed_suffix'])
    if arm=='dictionary':
        morph=view['metadata'][word]['morph']
        result.extend(f'm:{key}={val}' for key,values in sorted(morph.items()) for val in sorted(values))
        if not morph:result.append('dictionary_missing')
    return result


def pair_features(view,child,parent,arm,masked_type=None):
    n=len(view['tokens']);distance=parent-child;absolute=abs(distance)
    f=['bias',f'direction={int(distance>0)}',f'distance={min(absolute,6)}',f'length={min(n//8,7)}',
       f'child_position={min(3,4*child//n)}',f'parent_position={min(3,4*parent//n)}',f'directed_distance={max(-4,min(4,distance))}']
    if arm!='geometry':
        a=view['tokens'][child];b=view['tokens'][parent]
        if a!=masked_type and b!=masked_type:
            f.append(f'same_type={a==b}')
            if arm in ('ending_blind','ending_exposed','dictionary'):f.append(f'same_ending={a[-2:]==b[-2:]}')
    endpoint=[]
    for name,pos in [('c',child),('p',parent)]:
        values=token_features(view,pos,arm,masked_type);endpoint.append(values)
        f.extend(name+':'+value for value in values)
        for delta in (-1,1):f.extend(f'{name}{delta}:'+value for value in token_features(view,pos+delta,arm,masked_type))
    f.extend('cross:'+a+'|'+b for a in endpoint[0] for b in endpoint[1])
    return f


def masked_number_features(view,pos,arm):
    # Mask the complete central word type, including its other local occurrences.
    # No own ending, length, dictionary reading, or identity reaches this probe.
    n=len(view['tokens']);masked=view['tokens'][pos]
    result=['bias',f'position={min(3,4*pos//n)}',f'length={min(n//8,7)}']
    for delta in (-2,-1,1,2):result.extend(f'context{delta}:'+v for v in token_features(view,pos+delta,arm,masked))
    return result


@lru_cache(maxsize=300000)
def column(feature):return int.from_bytes(hashlib.blake2b(feature.encode(),digest_size=8).digest(),'little')%DIM


def matrix(rows):
    indices=[];indptr=[0]
    for row in rows:
        indices.extend(sorted({column(f) for f in row}));indptr.append(len(indices))
    return csr_matrix((np.ones(len(indices)),np.asarray(indices),np.asarray(indptr)),shape=(len(rows),DIM))


def candidates(n):return [(c,p) for c in range(n) for p in range(max(0,c-RADIUS),min(n,c+RADIUS+1)) if c!=p]


def fit(x,y,classes,regularization=.003):
    y=np.asarray(y);counts=np.bincount(y,minlength=classes);weight=np.sqrt(len(y)/(classes*np.maximum(counts,1)))[y];weight/=weight.mean()
    def objective(flat):
        w=flat.reshape(DIM,classes);logits=np.asarray(x@w);normalizer=logsumexp(logits,axis=1)
        loss=float(np.dot(weight,normalizer-logits[np.arange(len(y)),y])/len(y)+regularization*np.sum(w*w)/2)
        probabilities=np.exp(logits-normalizer[:,None]);probabilities[np.arange(len(y)),y]-=1;probabilities*=weight[:,None]/len(y)
        gradient=np.asarray(x.T@probabilities)+regularization*w
        return loss,gradient.ravel()
    result=minimize(objective,np.zeros(DIM*classes),jac=True,method='L-BFGS-B',options={'maxiter':180,'ftol':1e-8,'gtol':1e-5})
    if not result.success:raise ValueError('Relation fit failed: '+result.message)
    return {'weights':result.x.reshape(DIM,classes).tolist(),'iterations':result.nit,'loss':float(result.fun),'training_class_counts':counts.tolist()}


def probabilities(x,model):
    logits=np.asarray(x@np.asarray(model['weights']));return np.exp(logits-logsumexp(logits,axis=1)[:,None])


def decode(pairs,probabilities,threshold):
    best={}
    for (child,parent),values in zip(pairs,probabilities):
        label=int(np.argmax(values[1:]))+1;confidence=float(values[label])
        if child not in best or confidence>best[child][2]:best[child]=(parent,label,confidence)
    return [[c,p,label,confidence] for c,(p,label,confidence) in sorted(best.items()) if confidence>=threshold]
