"""Observable government and predicted-carrier context; target center masked."""
from voynich_smt.contextual_nominative import features as base

def bucket(d):return str(d) if d<=2 else '3-4' if d<=4 else '5-8'

def features(words,pos,finite,i,identities=False):
    out=base(pos,i)
    for side,step in [('left',-1),('right',1)]:
        js=[i+step*d for d in range(1,9) if 0<=i+step*d<len(pos)]
        for kind,predicate in [('adp',lambda j:pos[j]=='ADP'),('marker',lambda j:pos[j] in ('SCONJ','CCONJ')),('finite',lambda j:finite[j]>=.5)]:
            j=next((j for j in js if predicate(j)),None)
            if j is None:out.append(side+':'+kind+':NONE');continue
            prefix=side+':'+kind;out.append(prefix+':distance='+bucket(abs(j-i)))
            between=range(min(j,i)+1,max(j,i));nom=sum(pos[k] in ('NOUN','PROPN','ADJ','PRON') for k in between);marks=sum(pos[k] in ('SCONJ','CCONJ') for k in between)
            out.extend([prefix+':nominals='+str(min(2,nom)),prefix+':markers='+str(min(2,marks))])
            if kind=='finite':out.append(prefix+':confidence='+('high' if finite[j]>=.9 else 'medium'))
            if identities and kind!='finite':out.append(prefix+':word='+words[j]+':d='+bucket(abs(j-i)))
    return out
