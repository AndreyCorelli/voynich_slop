"""Unsupervised contextual classes and a normalized class-based word bigram.

Classes are learned from source contexts only; names/POS/lemmas are never read.
Unobserved forms share an explicit unknown class with positive reserved mass.
"""
from array import array
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from voynich_smt.data.corpus import digest
from .sparse_lm import SparseBigram, BOS


def learn_classes(bigram, *, k=32, contexts=512, dimensions=32, iterations=25, seed=23):
    import numpy as np
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import svds
    from scipy.spatial.distance import cdist
    if type(k) is not int or not 1<=k<255: raise ValueError('Class count must be in [1,254]')
    ids=[w for w,n in enumerate(bigram.counts[:-1]) if n]
    if not ids: raise ValueError('No observed forms')
    k=min(k,len(ids))
    if k<1 or contexts<1 or dimensions<1 or iterations<1: raise ValueError('Invalid class parameters')
    rank=sorted(ids,key=lambda w:(-bigram.counts[w],w))[:contexts]
    columns={w:i for i,w in enumerate(rank)};rows={w:i for i,w in enumerate(ids)}
    values=Counter()
    for (a,b),n in bigram.edges.items():
        if a==BOS or b==bigram.eos:continue
        if b in columns:values[rows[a],columns[b]]+=n
        if a in columns:values[rows[b],len(rank)+columns[a]]+=n
    r=[];c=[];v=[]
    total=sum(bigram.counts[:-1])
    for (row,col),n in values.items():
        neighbor=rank[col%len(rank)]
        pmi=max(0.,math.log(n*total/(bigram.counts[ids[row]]*bigram.counts[neighbor])))
        if pmi:r.append(row);c.append(col);v.append(pmi)
    matrix=coo_matrix((v,(r,c)),shape=(len(ids),2*len(rank))).tocsr()
    d=min(dimensions,min(matrix.shape)-1)
    if d>=1 and matrix.nnz:
        u,s,_=svds(matrix,k=d,random_state=seed)
        features=u*s
    else:features=np.ones((len(ids),1))
    features/=np.maximum(np.linalg.norm(features,axis=1,keepdims=True),1e-12)
    weights=np.sqrt(np.asarray([bigram.counts[w] for w in ids],dtype=float))
    rng=np.random.default_rng(seed)
    chosen=[int(rng.choice(len(ids),p=weights/weights.sum()))]
    nearest=np.full(len(ids),np.inf)
    while len(chosen)<k:
        nearest=np.minimum(nearest,((features-features[chosen[-1]])**2).sum(axis=1))
        mass=weights*nearest;mass[chosen]=0
        selected=int(rng.choice(len(ids),p=mass/mass.sum())) if mass.sum()>0 else next(i for i in range(len(ids)) if i not in chosen)
        chosen.append(selected)
    centers=features[chosen].copy();labels=np.zeros(len(ids),dtype=int)
    for _ in range(iterations):
        distances=cdist(features,centers,'sqeuclidean');new=distances.argmin(axis=1)
        # Force nonempty clusters even for identical toy feature vectors.
        for cluster in range(k):
            if not np.any(new==cluster):
                sizes=np.bincount(new,minlength=k)
                eligible=np.flatnonzero(sizes[new]>1)
                candidate=int(eligible[np.argmax(distances[eligible,new[eligible]]*weights[eligible])])
                new[candidate]=cluster
        unchanged=np.array_equal(labels,new);labels=new
        for cluster in range(k):
            members=labels==cluster
            centers[cluster]=np.average(features[members],axis=0,weights=weights[members])
        if unchanged:break
    mapping=array('B',[k])*bigram.size
    for word,cluster in zip(ids,labels):mapping[word]=int(cluster)
    metadata={'algorithm':'ppmi-svd-weighted-kmeans-v1','classes':k,'contexts':contexts,'dimensions':dimensions,
              'iterations':iterations,'seed':seed,'weight':'sqrt(source token count)','unknown_class':k}
    return mapping,metadata


class ClassWordModel:
    order=2
    objective_kind='class_word'

    def __init__(self,bigram,labels,class_lm,training):
        self.bigram=bigram;self.labels=array('B',labels);self.class_lm=class_lm;self.training=training
        self.unknown=training['unknown_class'];self.nclasses=class_lm.size
        if len(self.labels)!=bigram.size or any(c>=self.nclasses for c in self.labels):raise ValueError('Invalid class map')
        for w,n in enumerate(bigram.counts[:-1]):
            if bool(n)==(self.labels[w]==self.unknown):raise ValueError('Observed/unknown class mismatch')
        expected=Counter()
        for w,n in enumerate(bigram.counts[:-1]):expected[self.labels[w]]+=n
        if any(expected[c]!=class_lm.counts[c] for c in range(class_lm.size)) or class_lm.counts[-1]!=bigram.counts[-1]:
            raise ValueError('Class counts do not match parent corpus')
        self.capacities=Counter(self.labels)
        self.emissions=array('d',(1/bigram.unseen if bigram.unseen else 0. for _ in range(bigram.size)))
        for w,n in enumerate(bigram.counts[:-1]):
            if n:self.emissions[w]=n/class_lm.counts[self.labels[w]]
        self.emissions.append(1.)
        self.identity=digest({'objective':'class-word-v1','bigram':bigram.identity,'class_lm':class_lm.identity,
                              'labels':hashlib.sha256(self.labels.tobytes()).hexdigest(),'training':training})
        self._class_prob=tuple(tuple(class_lm.probability(a,b) for b in range(class_lm.size+1))
                               for a in range(BOS,class_lm.size))
        self._leaders={};self._first={}
        for w,n in enumerate(bigram.counts[:-1]):
            group=self.labels[w]
            if len(self._first.setdefault(group,[]))<16:self._first[group].append(w)
            if n:self._leaders.setdefault(group,[]).append(w)
        for group in self._leaders:self._leaders[group].sort(key=lambda w:(-self.emissions[w],w))
        self._leaders[self.unknown]=self._first.get(self.unknown,[])

    def __getattr__(self,name):return getattr(self.bigram,name)

    def probability(self,previous,word):
        self.bigram._context(previous);self.bigram._outcome(word)
        a=BOS if previous==BOS else self.labels[previous]
        b=self.class_lm.eos if word==self.eos else self.labels[word]
        return self._class_prob[a+1][b]*self.emissions[word]

    def base_probability(self,word):return self.bigram.base_probability(word)
    def score_chunks(self,chunks):return SparseBigram.score_chunks(self,chunks)
    def score(self,document):return self.score_chunks((document,))

    def retrieval_candidates(self,direction,count):
        # Exact top-K candidates lie among K leaders per class: class weights
        # are constant inside a class for either conditional direction.
        cache=getattr(self,'_retrieval_cache',None)
        if cache is None:self._retrieval_cache={};cache=self._retrieval_cache
        key=direction,count
        if key not in cache:
            groups=dict(self._leaders) if direction=='successors' else dict(self._first)
            if count>16:
                needed=([self.unknown] if direction=='successors' else list(self.capacities))
                for c in needed:groups[c]=[]
                for w,c in enumerate(self.labels):
                    if c in needed and len(groups[c])<count:groups[c].append(w)
            cache[key]=tuple(w for group in groups.values() for w in group[:count])
        return cache[key]

    @classmethod
    def train(cls,bigram,documents,**parameters):
        labels,training=learn_classes(bigram,**parameters)
        size=training['classes']+bool(bigram.unseen)
        internal=SimpleNamespace(size=size,identity=digest({'class_inventory':size,'labels':hashlib.sha256(labels.tobytes()).hexdigest()}))
        class_lm=SparseBigram.train(internal,((labels[w] for w in d) for d in documents),config=bigram.config)
        return cls(bigram,labels,class_lm,training)

    def save(self,path):
        self.bigram.save(path)
        clm=self.class_lm
        metadata={'sha256':self.identity,'training':self.training,'inventory':clm.inventory_sha256,
                  'training_sha256':clm.training_sha256,'counts':list(clm.counts),
                  'edges':[(a,b,n) for (a,b),n in sorted(clm.edges.items())]}
        with sqlite3.connect(path) as connection:
            connection.execute('CREATE TABLE class_model (metadata TEXT NOT NULL, labels BLOB NOT NULL)')
            connection.execute('INSERT INTO class_model VALUES (?,?)',(json.dumps(metadata),self.labels.tobytes()))

    @classmethod
    def load(cls,path,inventory):
        bigram=SparseBigram.load(path,inventory)
        with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as connection:
            metadata,blob=connection.execute('SELECT metadata,labels FROM class_model').fetchone();metadata=json.loads(metadata)
        clm=SparseBigram(metadata['inventory'],metadata['counts'],{(a,b):n for a,b,n in metadata['edges']},bigram.config,metadata['training_sha256'])
        result=cls(bigram,array('B',blob),clm,metadata['training'])
        if result.identity!=metadata['sha256']:raise ValueError('Class model identity mismatch')
        return result
