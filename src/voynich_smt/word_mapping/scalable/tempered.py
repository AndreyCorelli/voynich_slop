"""Experimental unnormalized objective with weaker unigram frequency pressure.

Retrieval probabilities stay normalized and unchanged. Only dictionary scoring
changes: S_alpha = S_LM + (alpha - 1) sum_tokens log q(word).
EOS is excluded. This is a heuristic score, not a log likelihood.
"""
import json
import math
import sqlite3
from functools import lru_cache
from voynich_smt.data.corpus import digest


class FrequencyTempered:
    order = 2

    def __init__(self, bigram, alpha):
        if getattr(bigram, 'order', 2) != 2 or not math.isfinite(alpha) or not 0 <= alpha <= 1:
            raise ValueError('Expected a bigram and alpha in [0,1]')
        self.bigram, self.alpha = bigram, alpha
        self.identity = digest({'objective': 'frequency-tempered-v1', 'parent': bigram.identity, 'alpha': alpha})
        self.score_adjustment = lru_cache(maxsize=65536)(self._adjustment)

    def __getattr__(self, name):
        return getattr(self.bigram, name)

    def _adjustment(self, word):
        return 0. if word == self.eos else (self.alpha - 1) * math.log(self.base_probability(word))

    def score_chunks(self, chunks):
        adjustment = []
        def adjusted():
            for chunk in chunks:
                def words(chunk=chunk):
                    for word in chunk:
                        adjustment.append(self.score_adjustment(word))
                        yield word
                yield words()
        original = self.bigram.score_chunks(adjusted())
        return original + math.fsum(adjustment)

    def score(self, document):
        return self.score_chunks((document,))

    def save(self, path):
        self.bigram.save(path)
        with sqlite3.connect(path) as connection:
            connection.execute('CREATE TABLE tempered_metadata (metadata TEXT NOT NULL)')
            connection.execute('INSERT INTO tempered_metadata VALUES (?)',
                               (json.dumps({'alpha': self.alpha, 'sha256': self.identity}),))
