"""Separate source-only eligibility, number and person candidate predictors."""
from collections import Counter,defaultdict
import math
from voynich_smt.source_morphology import group,labels,label as joint_label
from voynich_smt.construction_interventions import readings_key

FEATURES=('role','number','person')
VALUES={'role':('NO','YES'),'number':('Sing','Plur'),'person':('1','2','3')}
POLICIES=('top1','set95','set99','total95','total99')


def target(token,feature,supervision):
    g=group(token['pos']);fs=token['features']
    if g is None or (feature=='person' and g=='nominal'):return None
    if supervision=='matched':
        y=joint_label(token)
        if y is None:return None
        if feature=='role':return 'NO' if y=='OTHER' else 'YES'
        if y=='OTHER':return None
        return y.split(':')[0 if feature=='number' else 1]
    if supervision!='expanded':raise ValueError('invalid supervision')
    if feature=='role':
        value=fs.get('VerbForm' if g=='verbal' else 'Case','')
        if not value or ',' in value:return None
        return 'YES' if value==('Fin' if g=='verbal' else 'Nom') else 'NO'
    value=fs.get('Number' if feature=='number' else 'Person','')
    return value if value in VALUES[feature] else None


def fit(sentences,supervision):
    totals=defaultdict(Counter);words=defaultdict(Counter);suffixes=defaultdict(Counter);counts=Counter()
    for tokens in sentences:
        for token in tokens:
            g=group(token['pos'])
            for feature in FEATURES:
                y=target(token,feature,supervision)
                if y is None:continue
                key=feature+'/'+g;totals[key][y]+=1;words[feature+'/'+readings_key(token)][y]+=1;counts[key]+=1
                for length in range(1,min(4,len(token['word']))+1):suffixes[key+'\t'+str(length)+'\t'+token['word'][-length:]][y]+=1
    return dict(supervision=supervision,totals={k:dict(v) for k,v in totals.items()},words={k:dict(v) for k,v in words.items()},suffixes={k:dict(v) for k,v in suffixes.items()},training_labels=dict(counts),pseudocount=2.,minimum_suffix_count=5)


def probabilities(model,word,pos,feature):
    g=group(pos)
    if g=='nominal' and feature=='person':return [0.,0.,1.]
    classes=VALUES[feature];key=feature+'/'+g;counts=model['totals'].get(key,{});n=sum(counts.values());prior=[(counts.get(c,0)+.5)/(n+.5*len(classes)) for c in classes];backoff=prior
    for length in range(min(4,len(word)),0,-1):
        counts=model['suffixes'].get(key+'\t'+str(length)+'\t'+word[-length:],{});n=sum(counts.values())
        if n>=5:
            backoff=[(counts.get(c,0)+2*p)/(n+2) for c,p in zip(classes,prior)];break
    counts=model['words'].get(feature+'/'+word+'\t'+pos,{});n=sum(counts.values())
    return [(counts.get(c,0)+2*p)/(n+2) for c,p in zip(classes,backoff)]


def calibrate(model,sentences):
    scores=defaultdict(list)
    for tokens in sentences:
        for token in tokens:
            for feature in FEATURES:
                y=target(token,feature,model['supervision'])
                if y is None:continue
                g=group(token['pos']);p=probabilities(model,token['word'],token['pos'],feature);scores[feature+'/'+g+'/'+y].append(1-p[VALUES[feature].index(y)])
    policies={}
    for name in POLICIES[1:]:
        alpha=.05 if name.endswith('95') else .01;allocated=name.startswith('total');records={}
        for g in ('nominal','pronoun','verbal'):
            m=2 if g=='nominal' else 3;feature_alpha=alpha/m if allocated else alpha
            for feature in FEATURES:
                if feature=='person' and g=='nominal':continue
                for c in VALUES[feature]:
                    key=feature+'/'+g+'/'+c;values=sorted(scores[key]);n=len(values);rank=math.ceil((n+1)*(1-feature_alpha));cutoff=values[rank-1] if rank<=n else 1.;records[key]=dict(n=n,rank=rank,feature_alpha=feature_alpha,threshold=max(0.,1-cutoff))
        policies[name]=dict(alpha=alpha,allocated=allocated,classes=records)
    return policies


def predict(model,policies,word,pos):
    g=group(pos)
    if g is None:return None
    p={feature:probabilities(model,word,pos,feature) for feature in FEATURES};joint=[]
    for c in labels(g):
        if c=='OTHER':joint.append(p['role'][0]);continue
        n,person=c.split(':');joint.append(p['role'][1]*p['number'][VALUES['number'].index(n)]*p['person'][VALUES['person'].index(person)])
    sets={'top1':[labels(g)[max(range(len(joint)),key=lambda i:joint[i])]]};feature_sets={}
    for name,policy in policies.items():
        fs={}
        for feature in FEATURES:
            if feature=='person' and g=='nominal':fs[feature]=['3'];continue
            fs[feature]=[c for c,v in zip(VALUES[feature],p[feature]) if v+1e-12>=policy['classes'][feature+'/'+g+'/'+c]['threshold']]
        candidates=[]
        if 'NO' in fs['role']:candidates.append('OTHER')
        if 'YES' in fs['role']:candidates.extend(n+':'+person for n in fs['number'] for person in fs['person'])
        sets[name]=candidates;feature_sets[name]=fs
    return dict(probabilities=joint,component_probabilities=p,sets=sets,feature_sets=feature_sets)
