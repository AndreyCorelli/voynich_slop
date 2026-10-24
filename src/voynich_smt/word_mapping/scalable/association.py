"""Experimental skip-association graph alignment; not a language likelihood.

Compare clipped smoothed log observed/independent pair ratios in target and source.
Reliability weights depend only on public pair counts. No true key enters scoring.
"""
from collections import Counter
from functools import lru_cache
import json
import math
import sqlite3
from pathlib import Path

from voynich_smt.data.corpus import digest


def pair_counts(document,distances):
    document=tuple(document)
    counts=Counter()
    for lag in distances:
        counts.update(zip(document,document[lag:]))
    return counts


def association_factors(pairs, *, clip=3., shrinkage=5.):
    outgoing,incoming=Counter(),Counter();total=sum(pairs.values())
    for (a,b),n in pairs.items(): outgoing[a]+=n;incoming[b]+=n
    factors={}
    for (a,b),n in pairs.items():
        expected=outgoing[a]*incoming[b]/total
        value=max(-clip,min(clip,math.log((n+1)/(expected+1))))
        factors[a,b]=(value,n/(n+shrinkage))
    return factors


class AssociationModel:
    order=2
    objective_kind='association'

    def __init__(self,bigram,pairs,*,distances=(1,2,4),clip=3.,shrinkage=5.):
        if getattr(bigram,'objective_kind',None) or getattr(bigram,'order',2)!=2:
            raise ValueError('Association requires original bigram resources')
        self.distances=tuple(distances)
        if not self.distances or tuple(sorted(set(self.distances)))!=self.distances or any(type(d) is not int or d<1 for d in self.distances):
            raise ValueError('Invalid association distances')
        if not math.isfinite(clip) or clip<=0 or not math.isfinite(shrinkage) or shrinkage<=0:
            raise ValueError('Invalid association constants')
        self.bigram,self.clip,self.shrinkage=bigram,clip,shrinkage
        self.pairs=dict(pairs);self.outgoing=Counter();self.incoming=Counter()
        for (a,b),n in self.pairs.items():
            if type(a) is not int or type(b) is not int or not 0<=a<bigram.size or not 0<=b<bigram.size or type(n) is not int or n<1 or not bigram.counts[a] or not bigram.counts[b]:
                raise ValueError('Invalid association pair')
            self.outgoing[a]+=n;self.incoming[b]+=n
        self.pair_total=sum(self.pairs.values())
        if not self.pair_total: raise ValueError('Empty association training')
        self.identity=digest({'objective':'skip-association-v1','bigram':bigram.identity,
                              'distances':self.distances,'clip':clip,'shrinkage':shrinkage,
                              'pairs':[(a,b,n) for (a,b),n in sorted(self.pairs.items())]})
        self.value=lru_cache(maxsize=262144)(self._value)

    def __getattr__(self,name): return getattr(self.bigram,name)

    def _value(self,a,b):
        expected=self.outgoing[a]*self.incoming[b]/self.pair_total
        return max(-self.clip,min(self.clip,math.log((self.pairs.get((a,b),0)+1)/(expected+1))))

    def score_chunks(self,chunks):
        document=tuple(w for chunk in chunks for w in chunk)
        if not document or any(type(w) is not int or not 0<=w<self.size for w in document):
            raise ValueError('Expected a nonempty inventory-ID document')
        factors=association_factors(pair_counts(document,self.distances),clip=self.clip,shrinkage=self.shrinkage)
        return math.fsum(-weight*(target-self.value(a,b))**2 for (a,b),(target,weight) in factors.items())

    def score(self,document): return self.score_chunks((document,))

    def save(self,path):
        self.bigram.save(path)
        with sqlite3.connect(path) as connection:
            connection.execute('CREATE TABLE associations (a INTEGER,b INTEGER,n INTEGER,PRIMARY KEY(a,b)) WITHOUT ROWID')
            connection.executemany('INSERT INTO associations VALUES (?,?,?)',((a,b,n) for (a,b),n in self.pairs.items()))
            connection.execute('CREATE TABLE association_metadata (metadata TEXT NOT NULL)')
            connection.execute('INSERT INTO association_metadata VALUES (?)',(json.dumps(
                {'distances':self.distances,'clip':self.clip,'shrinkage':self.shrinkage,'sha256':self.identity}),))

    @classmethod
    def load(cls,path,inventory):
        from .sparse_lm import SparseBigram
        bigram=SparseBigram.load(path,inventory)
        with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as connection:
            metadata=json.loads(connection.execute('SELECT metadata FROM association_metadata').fetchone()[0])
            pairs={(a,b):n for a,b,n in connection.execute('SELECT a,b,n FROM associations')}
        result=cls(bigram,pairs,distances=metadata['distances'],clip=metadata['clip'],shrinkage=metadata['shrinkage'])
        if result.identity!=metadata['sha256']: raise ValueError('Association identity mismatch')
        return result
