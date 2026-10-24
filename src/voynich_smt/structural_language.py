"""Ambiguity-marginalized morphological sequence model, with no plaintext key.

A statistical structural proxy, not a dependency parser. Equal signature sets
have equal emissions; closed-class words retain their surface identities.
"""
from collections import Counter
import math

from voynich_smt.structural_oracle import signatures, CONTENT, FUNCTION

BOS = ('BOS',)
EOS = ('EOS',)
UNK = ('UNK',)


def logsumexp(values):
    values = tuple(values)
    maximum = max(values)
    return maximum + math.log(sum(math.exp(v-maximum) for v in values))


class StructuralLanguageModel:
    def __init__(self, entries, *, alpha=.1, backoff=.2):
        if not alpha > 0 or not 0 < backoff < 1:
            raise ValueError('Invalid smoothing')
        self.profiles = {word: signatures(analyses) for word, analyses in entries.items()}
        self.alpha, self.backoff = alpha, backoff
        self.unigram, self.bigram, self.context = Counter(), Counter(), Counter()
        self.states = {EOS, UNK}
        self.fitted = False

    def emissions(self, word):
        profile = self.profiles.get(word, frozenset())
        if not profile:
            return (UNK,)
        # All candidates with a closed-class analysis are lexicalized. Same rule
        # used for every word, without reference to gold or a proposed dictionary.
        if any(s[0] in FUNCTION or s[0] not in CONTENT for s in profile):
            return (('FUNCTION', word),)
        return tuple(sorted(profile, key=repr))

    def fit(self, segments):
        if self.fitted:
            raise ValueError('Already fitted')
        for segment in segments:
            if not segment:
                continue
            previous = (BOS,)
            for word in (*segment, None):
                current = (EOS,) if word is None else self.emissions(word)
                self.states.update(current)
                for b in current:
                    self.unigram[b] += 1/len(current)
                for a in previous:
                    self.context[a] += 1/len(previous)
                    for b in current:
                        self.bigram[a, b] += 1/(len(previous)*len(current))
                previous = current
        if not self.unigram:
            raise ValueError('Empty training corpus')
        self.total = sum(self.unigram.values())
        self.fitted = True
        return self

    def log_transition(self, a, b):
        # OUTSIDE is one reserved training-unseen state: unseen candidates have
        # the same smoothed probability regardless of dictionary size.
        if b not in self.states:
            b = ('OUTSIDE',)
        size = len(self.states)+1
        unigram = (self.unigram[b]+self.alpha)/(self.total+self.alpha*size)
        conditional = (self.bigram[a, b]+self.alpha)/(self.context[a]+self.alpha*size)
        return math.log(self.backoff*unigram+(1-self.backoff)*conditional)

    def score(self, segments):
        if not self.fitted:
            raise ValueError('Fit model before scoring')
        total = 0.
        for segment in segments:
            if not segment:
                continue
            forward = {BOS: 0.}
            for word in (*segment, None):
                emission = (EOS,) if word is None else self.emissions(word)
                normalization = math.log(len(emission))
                forward = {b: logsumexp(v+self.log_transition(a,b) for a,v in forward.items())-normalization
                           for b in emission}
            total += forward[EOS]
        return total
