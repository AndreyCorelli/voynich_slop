"""Label-free, nested word-type perturbations and compact morphology supports."""
import numpy as np
from voynich_smt.construction_interventions import compatible,NOMINAL
from voynich_smt.relational_compatibility import expand

STATES=tuple((n,p) for n in ('Sing','Plur') for p in ('1','2','3'))


def relevant(pos,row):
    return (pos in NOMINAL and compatible(row[0],'Nom')) or (pos in ('VERB','AUX') and row[3]=='Fin')


def support(rows,pos):
    return {(n,p) for row in rows if relevant(pos,row) for n in expand(row[1],('Sing','Plur')) for p in expand(row[2],('1','2','3'))}


def schedule(lexicon,keys,seed):
    rng=np.random.default_rng(seed);plans={}
    for key in sorted(set(keys)):
        rows=lexicon.get(key,[]);pos=key.split('\t')[1];present=support(rows,pos);variants=[]
        for row in rows:
            if not relevant(pos,row):continue
            for field,allowed in ((1,('Sing','Plur')),(2,('1','2','3'))):
                if field==2 and pos in ('NOUN','PROPN'):continue
                if row[field] not in allowed:continue
                for alt in allowed:
                    if alt==row[field]:continue
                    changed=list(row);changed[field]=alt
                    if support([changed],pos)-present:variants.append(dict(original=list(row),extra=changed,field='number' if field==1 else 'person'))
        if variants:plans[key]=variants[int(rng.integers(len(variants)))]
    order=rng.permutation(sorted(plans)).tolist()
    return dict(seed=seed,order=order,plans=plans)


def perturb(lexicon,plan,rate,mode):
    if not 0<=rate<=1 or mode not in ('extra','masked','deleted','substituted'):raise ValueError('invalid perturbation')
    selected=plan['order'][:int(rate*len(plan['order']))];result=dict(lexicon)
    for key in selected:
        rows=[list(r) for r in lexicon[key]];edit=plan['plans'][key]
        if mode=='extra':rows.append(edit['extra'])
        elif mode=='masked':
            pos=key.split('\t')[1];rows=[[case,'','3' if pos in ('NOUN','PROPN') else '',form] for case,number,person,form in rows]
        else:
            rows.remove(edit['original'])
            if mode=='substituted':rows.append(edit['extra'])
        result[key]=[list(r) for r in sorted(set(map(tuple,rows)))]
    return result,selected


def encode(candidates):
    blocks={}
    for s,v,sn,sp,vn,vp in candidates:
        bit=STATES.index((sn,sp))*6+STATES.index((vn,vp));blocks[s,v]=blocks.get((s,v),0)|(1<<bit)
    return [[s,v,mask] for (s,v),mask in sorted(blocks.items())]


def decode(blocks):
    result=[]
    for s,v,mask in blocks:
        for i,(sn,sp) in enumerate(STATES):
            for j,(vn,vp) in enumerate(STATES):
                if mask&(1<<(6*i+j)):result.append([s,v,sn,sp,vn,vp])
    return result


def link_summary(blocks,reference):
    pairs={(s,v):mask for s,v,mask in blocks};pair=tuple(reference[:2]);mask=pairs.get(pair,0);bit=6*STATES.index(tuple(reference[2:4]))+STATES.index(tuple(reference[4:6]));ref=bool(mask&(1<<bit))
    def resolved(field):
        choices={p[field] for p in pairs};return len(choices)==1 and reference[field] in choices
    cross={}
    for field,name in ((0,'subject'),(1,'predicate')):
        other=1-field;filtered={p[other] for p in pairs if p[field]==reference[field]};cross[name]=len(filtered)==1 and reference[other] in filtered and not resolved(other)
    return dict(links=len(pairs),reference_exact=ref,reference_link=pair in pairs,unique_correct=len(pairs)==1 and pair in pairs,false_unique=len(pairs)==1 and pair not in pairs,new_opposite=cross)
