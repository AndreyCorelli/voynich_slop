"""Source-only construction-profile transfer, excluding all in-bearing subtrees.

Profiles use dependency/POS/case frames, other prepositions, and argument lemmas.
They never contain predicate identity features or in-complement case evidence.
"""
from collections import Counter,defaultdict
import math
import numpy as np
from voynich_smt.predicate_case import fit


def build_profiles(sentences):
    profiles=defaultdict(Counter);occurrences=Counter();excluded=0
    for tokens in sentences:
        children=defaultdict(list)
        for i,t in enumerate(tokens):
            if t['head'] is not None:children[t['head']].append(i)
        # Mark every ancestor of an in marker, using a visited set for cycles.
        contains_in=set()
        for i,t in enumerate(tokens):
            if t['pos']!='ADP' or t['word']!='in':continue
            node=i;seen=set()
            while node is not None and node not in seen:
                seen.add(node);contains_in.add(node);node=tokens[node]['head']
        for i,t in enumerate(tokens):
            if t['pos'] not in ('VERB','AUX') or not t['lemma']:continue
            lemma=t['lemma'];occurrences[lemma]+=1
            for j in children[i]:
                if j in contains_in:excluded+=1;continue
                child=tokens[j];rel=child['rel'];pos=child['pos']
                if rel in ('punct','discourse','cc','mark'):continue
                profiles[lemma][f'frame:{rel}:{pos}']+=1
                if child['case']:profiles[lemma][f'case:{rel}:{child["case"]}']+=1
                if pos in ('NOUN','PROPN') and child['lemma']:profiles[lemma][f'argument:{rel}:{child["lemma"]}']+=1
                for z in children[j]:
                    prep=tokens[z]
                    if prep['pos']=='ADP' and prep['rel']=='case' and prep['word']!='in':profiles[lemma][f'prep:{prep["word"]}:{child["case"] or "_"}']+=1
    return dict(profiles={k:dict(v) for k,v in profiles.items()},occurrences=dict(occurrences),excluded_subtrees=excluded)


def vectorize(profiles):
    vocabulary=sorted({f for row in profiles.values() for f in row});index={f:i for i,f in enumerate(vocabulary)};df=Counter(f for row in profiles.values() for f in row);n=len(profiles);vectors={}
    for lemma,row in profiles.items():
        v=np.zeros(len(vocabulary))
        for f,count in row.items():v[index[f]]=(1+math.log(count))*(1+math.log((1+n)/(1+df[f])))
        norm=np.linalg.norm(v)
        if norm:vectors[lemma]=v/norm
    return vectors


def train(records,profiles,k=5,strength=4.):
    model=fit(records,strength);model.update(profiles=profiles,k=k)
    return model


def transfer(model,predicate,vectors=None):
    """Exclude the query lemma from donors even when it has training labels."""
    vectors=vectorize(model['profiles']) if vectors is None else vectors
    if predicate not in vectors:return model['base'],[]
    neighbors=[]
    for lemma,counts in model['counts'].items():
        if lemma==predicate or lemma not in vectors:continue
        similarity=float(np.dot(vectors[predicate],vectors[lemma]))
        if similarity>1e-12:neighbors.append((lemma,similarity,counts))
    neighbors.sort(key=lambda x:(-x[1],x[0]));neighbors=neighbors[:model['k']]
    if not neighbors:return model['base'],[]
    # Each donor contributes a smoothed rate, rather than a frequency multiplier.
    rates=[(c.get('Acc',0)+model['strength']*model['base'])/(sum(c.values())+model['strength']) for _,_,c in neighbors];weights=np.array([s for _,s,_ in neighbors]);p=float(np.dot(weights,rates)/weights.sum())
    return p,[dict(predicate=lemma,similarity=s,counts=c) for lemma,s,c in neighbors]


def probability(model,predicate,hybrid=True,vectors=None):
    prior,_=transfer(model,predicate,vectors)
    if not hybrid:return prior
    c=model['counts'].get(predicate,{})
    return (c.get('Acc',0)+model['strength']*prior)/(sum(c.values())+model['strength'])
