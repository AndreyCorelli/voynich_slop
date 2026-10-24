"""Sparse absolute-discount trigram interpolation with bigram retrieval projection."""
from collections import Counter
from functools import lru_cache
import json
import math
from pathlib import Path
import sqlite3

from voynich_smt.data.corpus import digest
from .sparse_lm import BOS, SparseBigram


class InterpolatedTrigram:
    order = 3

    def __init__(self, bigram, triples, *, weight=.5, discount=.5):
        if not math.isfinite(weight) or not 0 < weight <= 1:
            raise ValueError('Trigram weight must be in (0,1]')
        if not math.isfinite(discount) or not 0 < discount < 1:
            raise ValueError('Trigram discount must be in (0,1)')
        self.bigram, self.triples = bigram, dict(triples)
        self.weight, self.discount = weight, discount
        # Immutable projection attributes avoid repeated dynamic delegation.
        for name in ('size','eos','counts','edges','config','inventory_sha256','training_sha256',
                     'totals','distinct','unseen','probability','base_probability','_context','_outcome'):
            setattr(self,name,getattr(bigram,name))
        self.lower_probability=lru_cache(maxsize=262144)(bigram.probability)
        self.totals3, self.distinct3 = Counter(), Counter()
        projected = Counter()
        for (a,b,c), count in self.triples.items():
            bigram._context(a); bigram._context(b); bigram._outcome(c)
            if type(count) is not int or count < 1 or (b == BOS and (a != BOS or c == bigram.eos)):
                raise ValueError('Invalid trigram edge')
            self.totals3[a,b] += count
            self.distinct3[a,b] += 1
            projected[b,c] += count
        if dict(projected) != bigram.edges:
            raise ValueError('Trigram/bigram counts differ')

    def __getattr__(self, name):
        # Counts/edges/probability remain the bigram projection for retrieval.
        return getattr(self.bigram,name)

    def probability3(self, before, previous, word):
        self._context(before); self._context(previous); self._outcome(word)
        return self._probability3(before,previous,word)

    def _probability3(self, before, previous, word):
        # Internal scorer IDs are already validated; cache the lower-order pair,
        # which repeats much more often than complete trigram proposals.
        lower = self.lower_probability(previous,word)
        total = self.totals3.get((before,previous),0)
        if not total:
            return lower
        higher = (max(self.triples.get((before,previous,word),0)-self.discount,0)/total
                  + self.discount*self.distinct3[before,previous]/total*lower)
        return (1-self.weight)*lower + self.weight*higher

    def score_chunks(self, chunks):
        def terms():
            a,b,tokens = BOS,BOS,0
            for chunk in chunks:
                for word in chunk:
                    if type(word) is not int or not 0 <= word < self.size:
                        raise ValueError('Document must contain inventory word IDs only')
                    p = self.probability3(a,b,word)
                    if not tokens:
                        p /= 1-self.probability3(BOS,BOS,self.eos)
                    yield math.log(p)
                    a,b,tokens = b,word,tokens+1
            if not tokens:
                raise ValueError('Cannot score an empty document')
            yield math.log(self.probability3(a,b,self.eos))
        return math.fsum(terms())

    def score(self, document):
        return self.score_chunks((document,))

    @property
    def identity(self):
        return digest({'order':3,'bigram':self.bigram.identity,'weight':self.weight,
                       'discount':self.discount,'triples':[(a,b,c,n) for (a,b,c),n in sorted(self.triples.items())]})

    @classmethod
    def train(cls, inventory, documents, *, weight=.5, discount=.5, config=None):
        # documents must be a re-iterable factory; no full corpus materialization.
        bigram = SparseBigram.train(inventory,documents(),config=config)
        triples = Counter()
        for document in documents():
            a,b,length = BOS,BOS,0
            for word in document:
                triples[a,b,word] += 1
                a,b,length = b,word,length+1
            if not length:
                raise ValueError('Empty training document')
            triples[a,b,bigram.eos] += 1
        return cls(bigram,triples,weight=weight,discount=discount)

    def save(self,path):
        self.bigram.save(path)
        with sqlite3.connect(path) as connection:
            connection.execute('CREATE TABLE trigrams (a INTEGER,b INTEGER,c INTEGER,n INTEGER,PRIMARY KEY(a,b,c)) WITHOUT ROWID')
            connection.executemany('INSERT INTO trigrams VALUES (?,?,?,?)',((a,b,c,n) for (a,b,c),n in self.triples.items()))
            connection.execute('CREATE TABLE trigram_metadata (metadata TEXT NOT NULL)')
            connection.execute('INSERT INTO trigram_metadata VALUES (?)',(json.dumps(
                {'format_version':1,'weight':self.weight,'discount':self.discount,'sha256':self.identity}),))

    @classmethod
    def load(cls,path,inventory):
        path=Path(path)
        bigram = SparseBigram.load(path,inventory)
        with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as connection:
            metadata = json.loads(connection.execute('SELECT metadata FROM trigram_metadata').fetchone()[0])
            if metadata['format_version'] != 1:
                raise ValueError('Unknown trigram format')
            result = cls(bigram,{(a,b,c):n for a,b,c,n in connection.execute('SELECT a,b,c,n FROM trigrams')},
                         weight=metadata['weight'],discount=metadata['discount'])
        if result.identity != metadata['sha256']:
            raise ValueError('Trigram identity mismatch')
        return result


def load_model(path,inventory):
    path=Path(path)
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as connection:
        contrast = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='shuffle_contrast_metadata'").fetchone()
        factored = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='factored_model'").fetchone()
        classes = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='class_model'").fetchone()
        trigram = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='trigram_metadata'").fetchone()
        association = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='association_metadata'").fetchone()
        tempered = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tempered_metadata'").fetchone()
        metadata = json.loads(connection.execute("SELECT metadata FROM tempered_metadata").fetchone()[0]) if tempered else None
    if contrast:
        if factored or classes or association or trigram or tempered: raise ValueError('Conflicting objective metadata')
        from .shuffle_contrast import ShuffleContrast
        return ShuffleContrast.load(path,inventory)
    if factored:
        if classes or association or trigram or tempered: raise ValueError('Conflicting objective metadata')
        from .factored_lm import FactoredLatinModel
        return FactoredLatinModel.load(path,inventory)
    if classes:
        if association or trigram or tempered: raise ValueError('Conflicting objective metadata')
        from .classes import ClassWordModel
        return ClassWordModel.load(path,inventory)
    if association:
        if trigram or tempered: raise ValueError('Conflicting objective metadata')
        from .association import AssociationModel
        return AssociationModel.load(path,inventory)
    model = InterpolatedTrigram.load(path,inventory) if trigram else SparseBigram.load(path,inventory)
    if metadata:
        from .tempered import FrequencyTempered
        model = FrequencyTempered(model, metadata["alpha"])
        if model.identity != metadata["sha256"]:
            raise ValueError("Tempered objective identity mismatch")
    return model
