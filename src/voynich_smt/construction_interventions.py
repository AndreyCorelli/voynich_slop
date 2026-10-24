"""Unranked four-field PP lattices and explicit fact interventions.

A hypothesis is (left,right,nominal_head,case,verbal_ancestor_or_None).
Predicates are only constrained to occur outside the proposed phrase; this
module supplies no semantic/valency information linking a noun to a verb.
"""
from itertools import combinations

FIELDS=('boundary','head','case','predicate')
NOMINAL=frozenset(('NOUN','PROPN','PRON'))
PHRASE=frozenset(('NOUN','PROPN','PRON','ADJ','DET','NUM'))


def readings_key(token):return token['word']+'\t'+token['pos']


def morphology(sentences):
    lexicon={}
    for tokens in sentences:
        for t in tokens:
            fs=t['features'];reading=tuple(fs.get(k,'') for k in ('Case','Number','Gender'));lexicon.setdefault(readings_key(t),set()).add(reading)
    return {k:[list(r) for r in sorted(v)] for k,v in sorted(lexicon.items())}


def compatible(a,b):
    return not a or not b or bool(set(a.split(','))&set(b.split(',')))


def witness(tokens,left,right,head,case,lexicon,mask_case=False):
    def readings(i):
        values=lexicon.get(readings_key(tokens[i]),[])
        return [('',n,g) if mask_case else (c,n,g) for c,n,g in values]
    for c,n,g in readings(head):
        if not compatible(c,case):continue
        valid=True
        for i in range(left,right+1):
            if i==head:continue
            pos=tokens[i]['pos']
            if pos in ('ADJ','DET'):
                if not any(compatible(rc,case) and compatible(rn,n) and compatible(rg,g) for rc,rn,rg in readings(i)):valid=False;break
            elif pos in NOMINAL:
                if not any(compatible(rc,case) or compatible(rc,'Gen') for rc,_,_ in readings(i)):valid=False;break
        if valid:return True
    return False


def domains(tokens,prep,reference,max_span=8,head_window=8):
    n=len(tokens);heads={i for i,t in enumerate(tokens) if t['pos'] in NOMINAL and abs(i-prep)<=head_window};boundaries={(l,r) for l in range(max(0,prep-max_span+1),prep+1) for r in range(prep,min(n,l+max_span)) if r>l};predicates={i for i,t in enumerate(tokens) if t['pos'] in ('VERB','AUX')};predicates.add(None)
    additions=dict(head=reference['head'] not in heads,boundary=(reference['left'],reference['right']) not in boundaries,predicate=reference['predicate'] not in predicates)
    heads.add(reference['head']);boundaries.add((reference['left'],reference['right']));predicates.add(reference['predicate'])
    return dict(heads=sorted(heads),boundaries=[list(b) for b in sorted(boundaries)],predicates=sorted(predicates,key=lambda p:-1 if p is None else p),oracle_additions=additions)


def lattice(tokens,prep,domain,lexicon,mask_case=False):
    result=[];raw=0;pos_count=0
    for left,right in domain['boundaries']:
        heads=[h for h in domain['heads'] if left<=h<=right];predicates=[p for p in domain['predicates'] if p is None or p<left or p>right];raw+=len(heads)*2*len(predicates)
        if any(i!=prep and t['pos'] not in PHRASE for i,t in enumerate(tokens[left:right+1],left)):continue
        pos_count+=len(heads)*2*len(predicates)
        for head in heads:
            for case in ('Acc','Abl'):
                if witness(tokens,left,right,head,case,lexicon,mask_case):result.extend([[left,right,head,case,p] for p in predicates])
    return result,dict(geometry=raw,pos_compatible=pos_count,morphology_compatible=len(result))


def value(candidate,field):
    if field=='boundary':return tuple(candidate[:2])
    return candidate[{'head':2,'case':3,'predicate':4}[field]]


def interventions():return [tuple(c) for n in range(5) for c in combinations(FIELDS,n)]


def reveal(candidates,reference,fields):
    return [c for c in candidates if all(value(c,f)==value(reference,f) for f in fields)]


def summarize(candidates,reference,fields=()):
    survivors=reveal(candidates,reference,fields);unrevealed=[f for f in FIELDS if f not in fields]
    return dict(remaining=len(survivors),reference_retained=list(reference) in survivors,uniquely_correct=len(survivors)==1 and survivors[0]==list(reference),false_unique=len(survivors)==1 and survivors[0]!=list(reference),
                unrevealed_resolved={f:len({value(c,f) for c in survivors})==1 and value(survivors[0],f)==value(reference,f) for f in unrevealed},choices={f:len({value(c,f) for c in survivors}) for f in FIELDS})
