"""Injective global dictionary changes with transactional passage rescoring."""
from dataclasses import dataclass
import numpy as np

@dataclass
class Proposal:
    changes: dict
    sentence_features: dict
    totals: np.ndarray
    score: float

class PassageScorer:
    def __init__(self,segments,mapping,sentence_features,coefficients):
        self.segments=segments;self.mapping=dict(mapping);self.feature_fn=sentence_features
        self.coefficients=np.asarray(coefficients);self.weights=np.asarray([len(s) for s in segments],dtype=float);self.words=float(self.weights.sum())
        if not self.words or len(set(mapping.values()))!=len(mapping):raise ValueError('Nonempty passage and injective dictionary required')
        self.affected={}
        for i,s in enumerate(segments):
            for token in set(s):self.affected.setdefault(token,set()).add(i)
        self.features=[np.asarray(sentence_features(tuple(mapping[t] for t in s))) for s in segments]
        self.totals=sum((n*x for n,x in zip(self.weights,self.features)),np.zeros(len(self.coefficients)))
        self.score=float(self.totals@self.coefficients/self.words)

    def propose(self,changes):
        changes={k:v for k,v in changes.items() if self.mapping[k]!=v}
        updated={**self.mapping,**changes}
        if len(set(updated.values()))!=len(updated):raise ValueError('Dictionary collision')
        indices=set().union(*(self.affected.get(t,set()) for t in changes)) if changes else set()
        features={i:np.asarray(self.feature_fn(tuple(updated[t] for t in self.segments[i]))) for i in sorted(indices)}
        totals=self.totals.copy()
        for i,x in features.items():totals+=self.weights[i]*(x-self.features[i])
        return Proposal(changes,features,totals,float(totals@self.coefficients/self.words))

    def commit(self,proposal):
        self.mapping.update(proposal.changes)
        for i,x in proposal.sentence_features.items():self.features[i]=x
        self.totals=proposal.totals;self.score=proposal.score

    def full_score(self):
        totals=sum((n*np.asarray(self.feature_fn(tuple(self.mapping[t] for t in s))) for n,s in zip(self.weights,self.segments)),np.zeros(len(self.coefficients)))
        return float(totals@self.coefficients/self.words)
