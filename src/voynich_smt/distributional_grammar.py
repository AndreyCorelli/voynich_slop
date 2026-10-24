"""Anonymous corpus-context profiles and conservative relation skeletons.

Profiles use ciphertext equality, ending classes and common frequency-rank axes.
No plaintext spelling, dictionary reading or source annotation is consulted.
"""
from collections import Counter
import math
import numpy as np
from .cipher_relations import pair_features as baseline_pair_features

CONTEXT_DIM=4*34
CLUSTERS=8


def observations(views,shuffle=False,seed=2401):
    """Word/end counts of neighboring word ranks and ending ranks at +/-1,2."""
    rng=np.random.default_rng(seed);wc={};ec={};per_sentence=[];global_count=np.zeros(CONTEXT_DIM)
    for view in views:
        tokens=list(view['tokens'])
        if shuffle:rng.shuffle(tokens)
        local_w={};local_e={};local_global=np.zeros(CONTEXT_DIM)
        for i,w in enumerate(tokens):
            vector=np.zeros(CONTEXT_DIM)
            for block,delta in enumerate((-2,-1,1,2)):
                j=i+delta;off=block*34
                if not 0<=j<len(tokens):vector[off+32]=1;continue
                other=tokens[j]
                wr=min(15,view['word_stats']['ranks'][other]);er=min(15,view['ending_stats']['ranks'][other[-2:]])
                vector[off+wr]=1;vector[off+16+er]=1
            # Last coordinate in each block is unused; keep fixed dimension.
            for table,key in ((wc,w),(ec,w[-2:]),(local_w,w),(local_e,w[-2:])):
                if key not in table:table[key]=np.zeros(CONTEXT_DIM)
                table[key]+=vector
            global_count+=vector;local_global+=vector
        per_sentence.append((local_w,local_e,local_global))
    return dict(words=wc,endings=ec,sentences=per_sentence,global_count=global_count)


def normalized(counts,fallback,smoothing=4):
    return (counts+smoothing*fallback)/(counts.sum()+smoothing)


def profiles(obs,word,sentence=None):
    w=obs['words'][word].copy();e=obs['endings'][word[-2:]].copy();g=obs['global_count'].copy()
    if sentence is not None:
        lw,le,lg=obs['sentences'][sentence]
        w-=lw.get(word,0);e-=le.get(word[-2:],0);g-=lg
    assert min(w.min(),e.min(),g.min())>=-1e-8
    global_profile=g/g.sum() if g.sum() else np.full(CONTEXT_DIM,1/CONTEXT_DIM)
    ep=normalized(e,global_profile,4)
    wp=normalized(w,ep,4)
    return wp,ep,float(w.sum()),float(e.sum())


def kmeans(rows,k=CLUSTERS):
    """Deterministic farthest-first initialization; no ciphertext-name ordering."""
    x=np.asarray(rows)
    if not len(x):raise ValueError('No context profiles')
    centers=[x[0]]
    while len(centers)<min(k,len(x)):
        distance=np.min(np.sum((x[:,None,:]-np.asarray(centers)[None,:,:])**2,axis=2),axis=1)
        centers.append(x[int(np.argmax(distance))])
    centers=np.asarray(centers)
    for _ in range(40):
        labels=np.argmin(np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2),axis=1)
        new=np.asarray([x[labels==j].mean(axis=0) if np.any(labels==j) else centers[j] for j in range(len(centers))])
        if np.max(np.abs(new-centers))<1e-9:centers=new;break
        centers=new
    return centers.tolist()


def fit_prototypes(obs):
    words=list(obs['words']);endings=list(obs['endings']);wp=[];ep=[]
    for word in words:
        p,e,ws,es=profiles(obs,word)
        if ws>=12:wp.append(p)
    for ending in endings:
        count=obs['endings'][ending]
        if count.sum()>=12:ep.append(normalized(count,obs['global_count']/obs['global_count'].sum(),4))
    return dict(word=kmeans(wp),ending=kmeans(ep),dimension=CONTEXT_DIM,clusters=CLUSTERS)


def assignments(obs,prototypes,view,index):
    result={}
    for word in view['tokens']:
        if word in result:continue
        wp,ep,ws,es=profiles(obs,word,index);values={}
        for kind,p in (('word',wp),('ending',ep)):
            centers=np.asarray(prototypes[kind]);dist=np.sum((centers-p[None,:])**2,axis=1);cluster=int(np.argmin(dist))
            values[kind]=dict(cluster=cluster,distances=dist.tolist())
        values['support']=(ws,es);result[word]=values
    return result


def attach_profiles(views,prototypes,shuffle=False):
    obs=observations(views,shuffle=shuffle)
    return [{**v,'distribution':assignments(obs,prototypes,v,i)} for i,v in enumerate(views)]


def profile_features(view,pos):
    if not 0<=pos<len(view['tokens']):return ['boundary']
    item=view['distribution'][view['tokens'][pos]];result=[]
    for kind in ('word','ending'):
        values=item[kind];result.append(f'{kind}_cluster={values["cluster"]}')
        # Distances to shared training prototypes retain more information than
        # a hard class; coarse bins keep the old binary hashed learner unchanged.
        for j,d in enumerate(values['distances']):result.append(f'{kind}_prototype{j}={min(12,int(d*100))}')
    for kind,support in zip(('word','ending'),item['support']):result.append(f'{kind}_support={min(10,int(math.log2(1+support)))}')
    return result


def pair_features(view,child,parent,arm):
    if arm=='dictionary':return baseline_pair_features(view,child,parent,'dictionary')
    f=baseline_pair_features(view,child,parent,'ending_blind')
    if arm=='baseline':return f
    endpoint=[]
    for role,pos in (('c',child),('p',parent)):
        vals=profile_features(view,pos);endpoint.append(vals)
        f.extend('dist:'+role+':'+v for v in vals)
        for delta in (-1,1):f.extend(f'dist:{role}{delta}:'+v for v in profile_features(view,pos+delta))
    for a in endpoint[0]:
        if '_cluster=' not in a:continue
        for b in endpoint[1]:
            if '_cluster=' in b:f.append('dist_cross:'+a+'|'+b)
    return f


def consensus(pairs,member_probabilities):
    """Unanimous head/label predictions; retain competing-edge margin."""
    if not pairs:return []
    arrays=np.asarray(member_probabilities);children=sorted({c for c,p in pairs});result=[]
    for child in children:
        indices=[j for j,(c,p) in enumerate(pairs) if c==child];choices=[]
        for array in arrays:
            typed=array[indices,1:];maximum=float(typed.max());locations=np.argwhere(np.abs(typed-maximum)<1e-12)
            if len(locations)!=1:choices.append(None)
            else:
                row,col=locations[0];choices.append((indices[int(row)],int(col)+1))
        if choices[0] is None or any(choice!=choices[0] for choice in choices):continue
        idx,label=choices[0];mean=arrays.mean(axis=0);confidence=float(mean[idx,label])
        alternatives=[float(mean[j,l]) for j in indices for l in range(1,mean.shape[1]) if (j,l)!=(idx,label)]
        margin=confidence-max(alternatives,default=0)
        result.append([child,pairs[idx][1],label,confidence,margin])
    return result


def skeleton(edges,threshold,margin):
    """High-confidence partial forest; no forced root or completion edges."""
    selected=[];heads={}
    for edge in sorted(edges,key=lambda e:(-e[3],e[0],e[1],e[2])):
        c,p,label,confidence,gap=edge
        if confidence<threshold or gap<margin or c in heads:continue
        current=p;seen={c};cycle=False
        while current in heads:
            if current in seen:cycle=True;break
            seen.add(current);current=heads[current]
        if current in seen:cycle=True
        if cycle:continue
        heads[c]=p;selected.append(edge)
    return sorted(selected,key=lambda e:e[0])


def wilson_lower(tp,n):
    if not n:return 0.
    z=1.959963984540054;p=tp/n
    return float((p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n))
