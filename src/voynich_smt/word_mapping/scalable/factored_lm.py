"""Normalized word/lemma/grammar mixture with local analysis marginalization.

All channels normalize over the complete inventory plus EOS. Unsupported output
forms retain positive surface-prior probability. Counts are fractional expected
counts, not duplicated occurrences for every possible analysis.
"""
from collections import Counter, OrderedDict
from functools import lru_cache
import json
import hashlib
import math
from pathlib import Path
import sqlite3

import numpy as np

from voynich_smt.data.corpus import digest
from .sparse_lm import BOS, SparseBigram


class FactorChannel:
    def __init__(self, counts, base, offsets, states, weights, *, alpha=1., beta=1., reserve=.01,
                 edges=None):
        if not alpha>0 or not beta>0 or not 0<reserve<1:
            raise ValueError('Invalid factor smoothing')
        self.alpha,self.beta,self.reserve=alpha,beta,reserve
        self.offsets,self.states,self.weights=offsets,states,weights
        self.size=len(counts)-1; self.eos=self.size
        self.nstates=int(np.max(states))+2 if len(states) else 1
        self.endstate=self.nstates-1
        self.base=np.asarray(base,dtype=np.float64)
        self.counts=np.asarray(counts,dtype=np.float64)
        rowids=np.repeat(np.arange(self.size),np.diff(offsets).astype(np.int64))
        self.mass=np.bincount(states,weights=(self.counts[rowids]+beta*self.base[rowids])*weights,
                              minlength=self.nstates)
        self.mass[self.endstate]=self.counts[-1]+beta*self.base[-1]
        self.prior=self.mass/self.mass.sum()
        self.edges=dict(edges or {})
        self.totals=np.zeros(self.nstates)
        self.bos_total=0.
        for (a,b),n in self.edges.items():
            if a==BOS:self.bos_total+=n
            else:self.totals[a]+=n
        self.members=lru_cache(maxsize=65536)(self._members)
        # B(v)=sum_z prior(z) E(v|z); compute per output on demand.
        self.background=lru_cache(maxsize=65536)(self._background)

    def _members(self,word):
        if word==BOS:return ((BOS,1.),)
        if word==self.eos:return ((self.endstate,1.),)
        start,end=map(int,self.offsets[word:word+2]); result={}
        for state,weight in zip(self.states[start:end],self.weights[start:end]):
            state=int(state); result[state]=result.get(state,0.)+float(weight)
        return tuple(sorted(result.items()))

    def _background(self,word):
        # Emission numerator is count(word)+beta*q(word), apportioned by r(z|word).
        numerator=self.counts[word]+self.beta*self.base[word]
        return math.fsum(self.prior[z]*numerator*r/self.mass[z]
                         for z,r in self.members(word) if self.mass[z])

    def probability(self,previous,word):
        after=self.members(word); before=self.members(previous)
        if not before:
            p=self.background(word)
        else:
            numerator=self.counts[word]+self.beta*self.base[word]
            p=0.
            for a,ra in before:
                total=self.bos_total if a==BOS else self.totals[a]
                observed=math.fsum(self.edges.get((a,b),0.)*numerator*rb/self.mass[b]
                                   for b,rb in after if self.mass[b])
                p+=ra*(observed+self.alpha*self.background(word))/(total+self.alpha)
        return (1-self.reserve)*p+self.reserve*self.base[word]

    def fit_edges(self,word_edges):
        edges=Counter()
        for (u,v),count in word_edges.items():
            before=self.members(u); after=self.members(v)
            # Unknown source analyses provide no feature evidence. They are not
            # merged into one fake lemma/grammar state.
            for a,ra in before:
                for b,rb in after:edges[a,b]+=count*ra*rb
        self.edges=dict(edges); self.totals=np.zeros(self.nstates);self.bos_total=0.
        for (a,b),n in edges.items():
            if a==BOS:self.bos_total+=n
            else:self.totals[a]+=n


def analysis_weights(index,counts,*,supervised=None,iterations=3):
    """Source-only lexical ambiguity priors with bounded soft allocation.

    Supervised evidence is fractional per-token compatible-analysis counts.
    Uniform initial weights become empirical lemma/grammar-prior weights.
    Fixed iterations are a bounded estimator, not a claim of likelihood EM.
    """
    offsets=np.asarray(index.offsets); sizes=np.diff(offsets).astype(np.int64)
    rowids=np.repeat(np.arange(len(sizes)),sizes)
    weights=1./sizes[rowids] if len(rowids) else np.array([],dtype=float)
    evidence=np.zeros(len(weights))
    for position,n in (supervised or {}).items():evidence[int(position)]+=n
    frequencies=np.asarray(counts[:-1],dtype=float)
    trace=[]
    for step in range(iterations):
        tokenmass=frequencies[rowids]*weights
        lp=np.bincount(index.lemma,weights=tokenmass,minlength=len(index.labels['lemma']))+1.
        gp=np.bincount(index.grammar,weights=tokenmass,minlength=len(index.labels['grammar']))+1.
        scores=lp[index.lemma]*gp[index.grammar]
        norm=np.bincount(rowids,weights=scores,minlength=len(sizes))
        prior=scores/norm[rowids]
        # Each word gets one prior pseudo-observation. Annotation counts dominate
        # only when that word really has independently observed annotations.
        proposal=prior+evidence
        sums=np.bincount(rowids,weights=proposal,minlength=len(sizes))
        proposal/=sums[rowids]
        trace.append({'iteration':step+1,'max_weight_change':float(np.max(abs(proposal-weights))) if len(weights) else 0.})
        weights=proposal
    return weights,trace


class FactoredLatinModel:
    retrieval_is_exact=False

    def __init__(self,bigram,index,weights,*,mixture=(.5,.25,.25),alpha=1.,beta=1.,reserve=.01,
                 channel_edges=None,training=None):
        if len(mixture)!=3 or any(not math.isfinite(x) or x<0 for x in mixture) or not math.isclose(sum(mixture),1.):
            raise ValueError('Mixture must be a probability simplex')
        if len(weights)!=len(index.lemma) or not np.all(np.isfinite(weights)) or np.any(weights<=0):
            raise ValueError('Invalid ambiguity weights')
        sizes=np.diff(index.offsets).astype(np.int64)
        rows=np.repeat(np.arange(bigram.size),sizes)
        sums=np.bincount(rows,weights=weights,minlength=bigram.size)
        if np.any(abs(sums[sizes>0]-1)>1e-10):raise ValueError('Analysis weights do not normalize')
        self.bigram,self.index,self.weights=bigram,index,np.asarray(weights)
        self.mixture=tuple(mixture);self.alpha,self.beta,self.reserve=alpha,beta,reserve
        self.training=training or {}
        for name in ('size','eos','counts','edges','config','inventory_sha256','training_sha256',
                     'totals','distinct','unseen','base_probability','_context','_outcome'):
            setattr(self,name,getattr(bigram,name))
        base=np.fromiter((bigram.base_probability(i) for i in range(bigram.size+1)),float)
        channels=[]
        for k,states in enumerate((index.lemma,index.grammar)):
            channel=FactorChannel(bigram.counts,base,index.offsets,states,self.weights,
                     alpha=alpha,beta=beta,reserve=reserve,
                     edges=None if channel_edges is None else channel_edges[k])
            if channel_edges is None:channel.fit_edges(bigram.edges)
            channels.append(channel)
        self.channels=tuple(channels)
        self.factor_successors=[];self.factor_predecessors=[]
        for channel in channels:
            successors={};predecessors={}
            for (a,b),n in channel.edges.items():
                successors.setdefault(a,[]).append((b,n))
                predecessors.setdefault(b,[]).append((a,n))
            self.factor_successors.append(successors);self.factor_predecessors.append(predecessors)
        self._probability=lru_cache(maxsize=262144)(self._calculate)
        self._retrieval=OrderedDict()
        # Emission leaders per state. Source-only index; all forms remain eligible.
        self.leaders=[]
        for channel in channels:
            leaders={}
            order=sorted((i for i,c in enumerate(self.counts[:-1]) if c),key=lambda i:(-self.counts[i],i))
            for word in order:
                for state,_ in channel.members(word):
                    row=leaders.setdefault(state,[])
                    if len(row)<16:row.append(word)
            self.leaders.append(leaders)

    def _calculate(self,u,v):
        return self.mixture[0]*self.bigram.probability(u,v)+math.fsum(
               weight*channel.probability(u,v) for weight,channel in zip(self.mixture[1:],self.channels) if weight)

    def probability(self,u,v):
        self._context(u);self._outcome(v)
        return self._probability(u,v)

    def score_chunks(self,chunks):return SparseBigram.score_chunks(self,chunks)
    def score(self,document):return self.score_chunks((document,))

    def factor_candidates(self,direction,neighbor,count):
        key=(direction,neighbor,count)
        if key in self._retrieval:
            self._retrieval.move_to_end(key);return self._retrieval[key]
        words=set()
        for k,(channel,leaders) in enumerate(zip(self.channels,self.leaders)):
            relevant=dict(channel.members(neighbor))
            ranked=Counter()
            if direction.startswith('successors'):
                for a,ra in relevant.items():
                    for b,n in self.factor_successors[k].get(a,()):
                        ranked[b]+=ra*n/(channel.totals[a]+channel.alpha if a!=BOS else channel.bos_total+channel.alpha)
            else:
                for b,rb in relevant.items():
                    for a,n in self.factor_predecessors[k].get(b,()):
                        if a!=BOS:ranked[a]+=n*rb/(channel.totals[a]+channel.alpha)
            for state,_ in ranked.most_common(16):words.update(leaders.get(state,())[:count])
            for state in relevant:words.update(leaders.get(state,())[:count])
        result=tuple(sorted(words));self._retrieval[key]=result
        if len(self._retrieval)>256:self._retrieval.popitem(last=False)
        return result

    @property
    def identity(self):
        return digest({'kind':'factored-latin-v1','parent':self.bigram.identity,
             'morphology':self.index.identity,'mixture':self.mixture,'alpha':self.alpha,'beta':self.beta,
             'reserve':self.reserve,'weights':hashlib.sha256(self.weights.astype('<f8').tobytes()).hexdigest(),'training':self.training,
             'channels':[digest([(a,b,n) for (a,b),n in sorted(c.edges.items())]) for c in self.channels]})

    def save(self,path):
        self.bigram.save(path)
        metadata={'format_version':1,'morphology_path':str(self.index.path.resolve()),
          'morphology_sha256':self.index.identity,'mixture':self.mixture,'alpha':self.alpha,
          'beta':self.beta,'reserve':self.reserve,'training':self.training,'sha256':self.identity}
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE factored_model(metadata TEXT NOT NULL,weights BLOB NOT NULL)')
            db.execute('INSERT INTO factored_model VALUES (?,?)',(json.dumps(metadata),self.weights.astype('<f8').tobytes()))
            db.execute('CREATE TABLE factor_edges(channel INTEGER,a INTEGER,b INTEGER,n REAL,PRIMARY KEY(channel,a,b)) WITHOUT ROWID')
            for k,c in enumerate(self.channels):
                db.executemany('INSERT INTO factor_edges VALUES (?,?,?,?)',((k,a,b,n) for (a,b),n in c.edges.items()))

    @classmethod
    def load(cls,path,inventory):
        from .morphology_index import MorphologyIndex
        bigram=SparseBigram.load(path,inventory)
        with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
            meta,blob=db.execute('SELECT metadata,weights FROM factored_model').fetchone();meta=json.loads(meta)
            if meta['format_version']!=1:raise ValueError('Unknown factor model version')
            index=MorphologyIndex(meta['morphology_path'],inventory)
            if index.identity!=meta['morphology_sha256']:raise ValueError('Morphology model identity mismatch')
            edges=[{},{}]
            for k,a,b,n in db.execute('SELECT channel,a,b,n FROM factor_edges'):edges[k][a,b]=n
            result=cls(bigram,index,np.frombuffer(blob,dtype='<f8'),mixture=meta['mixture'],
                  alpha=meta['alpha'],beta=meta['beta'],reserve=meta['reserve'],training=meta['training'],channel_edges=edges)
            if result.identity!=meta['sha256']:raise ValueError('Factored model identity mismatch')
            return result
