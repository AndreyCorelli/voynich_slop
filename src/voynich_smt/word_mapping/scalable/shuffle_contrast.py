"""Frequency-matched ordering contrast, not normalized text likelihood.

S(key) = LL(decoded) - mean_k LL(fixed_shuffle_k(decoded)). Endpoints stay
fixed, so every shuffle has identical incoming/outgoing word margins and the
BOS/EOS terms cancel. Shuffles depend on positions, never on decoded identities.
Only sparse observed training-edge bonuses remain after exact row/column
cancellation. Unsupported all-unobserved dictionaries score exactly zero.
"""
from collections import Counter
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import sqlite3

from voynich_smt.data.corpus import digest


@lru_cache(maxsize=32)
def permutations(length,shuffles,seed):
    rng=random.Random(seed+length*1000003)
    result=[]
    for _ in range(shuffles):
        middle=list(range(1,max(1,length-1)))
        rng.shuffle(middle)
        result.append(tuple([0]+middle+([length-1] if length>1 else [])))
    return tuple(result)


def signed_pairs(document,*,shuffles=8,seed=2701):
    """Integer K*observed-minus-null multiplicities with exactly zero margins."""
    document=tuple(document)
    if not document:raise ValueError('Expected a nonempty document')
    counts=Counter({pair:n*shuffles for pair,n in Counter(zip(document,document[1:])).items()})
    for order in permutations(len(document),shuffles,seed):
        shuffled=tuple(document[i] for i in order)
        counts.subtract(zip(shuffled,shuffled[1:]))
    return {pair:n for pair,n in counts.items() if n}


class ShuffleContrast:
    order=2
    objective_kind='shuffle_contrast'
    distances=(1,)

    def __init__(self,bigram,*,shuffles=8,seed=2701,frequency_weight=0.):
        from .sparse_lm import SparseBigram
        if (type(bigram) is not SparseBigram
            or type(shuffles) is not int or shuffles<1 or type(seed) is not int
            or not math.isfinite(frequency_weight) or not 0<=frequency_weight<=1):
            raise ValueError('Expected original bigram and valid shuffle specification')
        self.bigram,self.shuffles,self.seed=bigram,shuffles,seed
        self.frequency_weight=frequency_weight
        identity={'objective':'endpoint-fixed-shuffle-contrast-v1',
             'parent':bigram.identity,'shuffles':shuffles,'seed':seed}
        if frequency_weight:identity['frequency_weight']=frequency_weight
        self.identity=digest(identity)
        self.pair_value=lru_cache(maxsize=262144)(self._pair_value)

    def __getattr__(self,name):return getattr(self.bigram,name)

    def _pair_value(self,a,b):
        n=self.bigram.edges.get((a,b),0)
        if not n:return 0.
        # log[P(b|a) / (lambda(a)*q(b))]. All lambda and q terms
        # cancel across the signed graph; this form avoids cancellation drift.
        d=self.config.discount
        return math.log1p(max(n-d,0.)/(d*self.distinct[a]*self.base_probability(b)))

    def pairs(self,document):return signed_pairs(document,shuffles=self.shuffles,seed=self.seed)

    def context_score(self,direction,neighbor,word):
        return self.pair_value(neighbor,word) if direction.startswith('successors') else self.pair_value(word,neighbor)

    def score_chunks(self,chunks):
        document=tuple(w for chunk in chunks for w in chunk)
        if not document or any(type(w) is not int or not 0<=w<self.size for w in document):
            raise ValueError('Expected nonempty inventory-ID document')
        contrast=math.fsum(n*self.pair_value(a,b)/self.shuffles for (a,b),n in self.pairs(document).items())
        return contrast+self.frequency_weight*math.fsum(math.log(self.base_probability(w)) for w in document)

    def score(self,document):return self.score_chunks((document,))

    def save(self,path):
        self.bigram.save(path)
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE shuffle_contrast_metadata(metadata TEXT NOT NULL)')
            db.execute('INSERT INTO shuffle_contrast_metadata VALUES (?)',(json.dumps({
                  'format_version':1,'shuffles':self.shuffles,'seed':self.seed,
                  'frequency_weight':self.frequency_weight,'sha256':self.identity}),))

    @classmethod
    def load(cls,path,inventory):
        from .sparse_lm import SparseBigram
        base=SparseBigram.load(path,inventory)
        with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
            meta=json.loads(db.execute('SELECT metadata FROM shuffle_contrast_metadata').fetchone()[0])
        if meta['format_version']!=1:raise ValueError('Unknown shuffle contrast format')
        model=cls(base,shuffles=meta['shuffles'],seed=meta['seed'],frequency_weight=meta.get('frequency_weight',0.))
        if model.identity!=meta['sha256']:raise ValueError('Shuffle contrast identity mismatch')
        return model
