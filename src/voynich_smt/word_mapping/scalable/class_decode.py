"""Coarse type-consistent class decoding with fitted cipher emissions.

S = class Markov log likelihood + sum_type n log n - sum_class N log N.
The emission term is the maximized categorical cipher-word likelihood per class.
Class capacities enforce that an injective word dictionary can realize a key.
"""
from collections import Counter
import math
import random

from .incremental import EventIndex, EOS
from .sparse_lm import BOS


def xlogx(n):return n*math.log(n) if n else 0.


class ClassDecoder:
    def __init__(self,model,stream,assignments):
        self.model=model;self.stream=stream;self.lm=model.class_lm
        self.index=EventIndex.build(stream);self.key=list(assignments)
        if len(self.key)!=stream.type_count or any(type(c) is not int or not 0<=c<model.nclasses for c in self.key):raise ValueError('Invalid class key')
        self.counts=Counter(c for d in stream.documents for c in d)
        self.mass=Counter();self.owners={c:set() for c in range(model.nclasses)}
        for cipher,cluster in enumerate(self.key):self.mass[cluster]+=self.counts[cipher];self.owners[cluster].add(cipher)
        if any(len(v)>model.capacities[c] for c,v in self.owners.items()):raise ValueError('Class capacity exceeded')
        self.constant=sum(xlogx(n) for n in self.counts.values())
        self.events=[self.event(e,{}) for e in self.index.events]
        self.score=math.fsum(self.events)+self.constant-sum(xlogx(n) for n in self.mass.values())

    def event(self,event,changes):
        a,b,n=event
        previous=BOS if a==BOS else changes.get(a,self.key[a])
        word=self.lm.eos if b==EOS else changes.get(b,self.key[b])
        p=self.lm.probability(previous,word)
        if a==BOS:p/=1-self.lm.probability(BOS,self.lm.eos)
        return n*math.log(p)

    def proposal(self,changes):
        changes={c:k for c,k in changes.items() if self.key[c]!=k}
        masses=Counter(self.mass);sizes={k:len(v) for k,v in self.owners.items()}
        for c,k in changes.items():
            if not 0<=k<self.model.nclasses:raise ValueError('Invalid class')
            masses[self.key[c]]-=self.counts[c];masses[k]+=self.counts[c]
            sizes[self.key[c]]-=1;sizes[k]+=1
        if any(n>self.model.capacities[k] for k,n in sizes.items()):raise ValueError('Class capacity exceeded')
        affected=sorted({i for c in changes for i in self.index.affected[c]})
        values=[(i,self.event(self.index.events[i],changes)) for i in affected]
        touched={self.key[c] for c in changes}|set(changes.values())
        delta=math.fsum(value-self.events[i] for i,value in values)+sum(xlogx(self.mass[k])-xlogx(masses[k]) for k in touched)
        return delta,changes,values,masses

    def commit(self,move):
        delta,changes,values,masses=move
        for c,k in changes.items():self.owners[self.key[c]].remove(c);self.owners[k].add(c);self.key[c]=k
        for i,value in values:self.events[i]=value
        self.mass=masses;self.score+=delta

    def full_score(self):
        ll=math.fsum(self.lm.score(self.key[c] for c in d) for d in self.stream.documents)
        mass=Counter()
        for c,n in self.counts.items():mass[self.key[c]]+=n
        return ll+self.constant-sum(xlogx(n) for n in mass.values())


def initialize_classes(stream,model,*,seed,steps=2000):
    from .state import DictionaryState
    rng=random.Random(seed+7000003)
    # Random full-inventory key is capacity-feasible and uses no plaintext.
    word_key=DictionaryState.random(stream,model,seed=seed)
    decoder=ClassDecoder(model,stream,[model.labels[w] for w in word_key.assignments])
    best=(decoder.score,tuple(decoder.key));counts=[decoder.counts[c] for c in range(stream.type_count)]
    for step in range(steps):
        cipher=rng.randrange(stream.type_count) if rng.random()<.5 else rng.choices(range(stream.type_count),weights=counts,k=1)[0]
        moves=[]
        for cluster in range(model.nclasses):
            changes={cipher:cluster}
            if cluster!=decoder.key[cipher] and len(decoder.owners[cluster])>=model.capacities[cluster]:
                other=rng.choice(sorted(decoder.owners[cluster]));changes[other]=decoder.key[cipher]
            moves.append(decoder.proposal(changes))
        move=max(moves,key=lambda m:m[0]) if rng.random()<.8 else rng.choice(moves)
        temperature=1.*(.05**(step/max(1,steps-1)))
        if move[0]>=0 or rng.random()<math.exp(max(-745.,move[0]/temperature)):
            decoder.commit(move)
            if decoder.score>best[0]:best=(decoder.score,tuple(decoder.key))
        if (step+1)%500==0 and abs(decoder.full_score()-decoder.score)>1e-7:raise ValueError('Class score drift')
    # Lift classes into one complete word key, preserving class and injectivity.
    groups={}
    for c,k in enumerate(best[1]):groups.setdefault(k,[]).append(c)
    assignments=[None]*stream.type_count
    for cluster,ciphers in groups.items():
        ciphers.sort(key=lambda c:(-decoder.counts[c],c))
        from itertools import islice
        candidates=(list(islice((w for w,k in enumerate(model.labels) if k==cluster),len(ciphers)))
                    if cluster==model.unknown else model._leaders[cluster][:len(ciphers)])
        for c,w in zip(ciphers,candidates):assignments[c]=w
    return DictionaryState.create(stream,model,assignments)
