"""Candidate-derived POS and a truth-free structured-utility diagnostic."""
from collections import Counter,defaultdict
import math
import numpy as np

POS_MAP={'N':('NOUN','PROPN'),'V':('VERB','AUX'),'VPAR':('VERB',),'SUPINE':('VERB',),'ADJ':('ADJ',),'PRON':('PRON',),'PREP':('ADP',),'CONJ':('CCONJ','SCONJ'),'ADV':('ADV',),'NUM':('NUM',),'INTERJ':('INTJ',)}


def pos_model(sentences):
    words=defaultdict(Counter);prior=Counter();counts=Counter()
    for tokens in sentences:
        for t in tokens:words[t['word']][t['pos']]+=1;prior[t['pos']]+=1;counts[t['word']]+=1
    return dict(words={w:dict(c) for w,c in words.items()},prior=dict(prior),counts=dict(counts),tokens=sum(counts.values()))


def candidate_pos(word,model,analyses):
    observed=model['words'].get(word,{})
    if observed:
        return max(observed,key=lambda p:(observed[p],model['prior'].get(p,0),p)),'source_word'
    allowed={p for r in analyses for p in POS_MAP.get(r['pos'],())}
    if not allowed:return 'X','unknown'
    return max(allowed,key=lambda p:(model['prior'].get(p,0),p)),'dictionary_prior'


def candidate_tokens(words,model,lexicon):
    tokens=[];origins=Counter()
    for word in words:
        p,origin=candidate_pos(word,model,lexicon.get(word,[]));origins[origin]+=1
        tokens.append(dict(word=word,pos=p,head=None,rel='?',features={},lemma='?'))
    return tokens,dict(origins)


def objective_value(frames,predictions,cutoff,penalty):
    edges=0.;counts=Counter()
    for r in frames:
        v=predictions[r['subject']]
        if v is not None:edges+=float(r['scores'][r['predicates'].index(v)]-cutoff);counts[v]+=1
    competition=penalty*sum(max(0,n-1) for n in counts.values())
    return dict(edge_utility=edges,competition_cost=competition,total=edges-competition,attached=sum(counts.values()))


def permutations(length,count=5,seed=6901):
    rng=np.random.default_rng(seed+length)
    return [rng.permutation(length).tolist() for _ in range(count)]


def structural_lift(original,shuffled):
    return float(original-np.mean(shuffled))


def map_cipher(cipher,mapping):return [mapping[c] for c in cipher]
