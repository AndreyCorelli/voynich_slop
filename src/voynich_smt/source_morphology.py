"""Source-only task morphology: word/suffix counts and calibrated candidate sets.

Inputs to inference are readable word forms and supplied POS, never morphology
or reference dependencies. OTHER means not nominative / not finite for this task.
"""
from collections import Counter,defaultdict
import math
from voynich_smt.construction_interventions import readings_key

ARMS=('dictionary','top1','set95','set99','all')


def group(pos):
    return 'nominal' if pos in ('NOUN','PROPN') else 'pronoun' if pos=='PRON' else 'verbal' if pos in ('VERB','AUX') else None


def labels(g):return ['OTHER']+[n+':'+p for n in ('Sing','Plur') for p in (('3',) if g=='nominal' else ('1','2','3'))]


def label(token):
    g=group(token['pos']);f=token['features']
    if g is None:return None
    if g in ('nominal','pronoun'):
        case=f.get('Case','')
        if not case or ',' in case:return None
        if case!='Nom':return 'OTHER'
    else:
        form=f.get('VerbForm','')
        if not form:return None
        if form!='Fin':return 'OTHER'
    n=f.get('Number','');p='3' if g=='nominal' else f.get('Person','')
    return n+':'+p if n in ('Sing','Plur') and p in ('1','2','3') else None


def fit(sentences):
    totals=defaultdict(Counter);words=defaultdict(Counter);suffixes=defaultdict(Counter);n=0
    for tokens in sentences:
        for t in tokens:
            y=label(t)
            if y is None:continue
            g=group(t['pos']);totals[g][y]+=1;words[readings_key(t)][y]+=1;n+=1
            for length in range(1,min(4,len(t['word']))+1):suffixes[g+'\t'+str(length)+'\t'+t['word'][-length:]][y]+=1
    return dict(totals={g:dict(v) for g,v in totals.items()},words={k:dict(v) for k,v in words.items()},suffixes={k:dict(v) for k,v in suffixes.items()},training_tokens=n,pseudocount=2.,minimum_suffix_count=5)


def probabilities(model,word,pos):
    g=group(pos)
    if g is None:return None
    classes=labels(g);counts=model['totals'].get(g,{});total=sum(counts.values());prior=[(counts.get(c,0)+.5)/(total+.5*len(classes)) for c in classes];backoff=prior
    for length in range(min(4,len(word)),0,-1):
        counts=model['suffixes'].get(g+'\t'+str(length)+'\t'+word[-length:],{});n=sum(counts.values())
        if n>=model['minimum_suffix_count']:
            backoff=[(counts.get(c,0)+2*p)/(n+2) for c,p in zip(classes,prior)];break
    counts=model['words'].get(word+'\t'+pos,{});n=sum(counts.values())
    return [(counts.get(c,0)+2*p)/(n+2) for c,p in zip(classes,backoff)]


def calibrate(model,sentences,alpha):
    scores=defaultdict(list)
    for tokens in sentences:
        for t in tokens:
            y=label(t)
            if y is None:continue
            g=group(t['pos']);p=probabilities(model,t['word'],t['pos']);scores[g+'/'+y].append(1-p[labels(g).index(y)])
    result={}
    for g in ('nominal','pronoun','verbal'):
        for c in labels(g):
            values=sorted(scores[g+'/'+c]);n=len(values);rank=math.ceil((n+1)*(1-alpha));cutoff=values[rank-1] if rank<=n else 1.
            result[g+'/'+c]=dict(n=n,rank=rank,score_cutoff=cutoff,threshold=max(0.,1-cutoff))
    return dict(alpha=alpha,classes=result)


def predict(model,policies,word,pos):
    g=group(pos)
    if g is None:return None
    classes=labels(g);p=probabilities(model,word,pos);observed=model['words'].get(word+'\t'+pos,{})
    sets=dict(dictionary=[c for c in classes if observed.get(c,0)] if observed else classes,top1=[classes[max(range(len(p)),key=lambda i:p[i])]],all=classes)
    for name in ('set95','set99'):sets[name]=[c for c,v in zip(classes,p) if v+1e-12>=policies[name]['classes'][g+'/'+c]['threshold']]
    return dict(probabilities=p,sets=sets,seen=bool(observed))


def domains(tokens,type_predictions,arm):
    subjects=[];predicates=[]
    for i,t in enumerate(tokens):
        g=group(t['pos'])
        if g is None:continue
        sets=type_predictions[readings_key(t)]['sets'][arm]
        for c in sets:
            if c=='OTHER':continue
            n,p=c.split(':');(predicates if g=='verbal' else subjects).append([i,n,p])
    return dict(subjects=subjects,predicates=predicates)
