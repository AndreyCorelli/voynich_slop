"""Explicit genitive roles and genuinely coupled finite subject/verb lattices."""
from itertools import product,combinations
from voynich_smt.construction_interventions import compatible,readings_key,PHRASE,NOMINAL

SV_FIELDS=('subject','predicate','subject_features','predicate_features')


def role_witness(tokens,left,right,head,case,lexicon):
    for hc,hn,hg in lexicon.get(readings_key(tokens[head]),[]):
        if not compatible(hc,case):continue
        roles={};valid=True
        for i in range(left,right+1):
            if i==head:continue
            pos=tokens[i]['pos'];readings=lexicon.get(readings_key(tokens[i]),[])
            if pos in ('ADJ','DET'):
                allowed=[]
                if any(compatible(c,case) and compatible(n,hn) and compatible(g,hg) for c,n,g in readings):allowed.append('agreeing_modifier')
                if any('Gen' in c.split(',') for c,_,_ in readings):allowed.append('genitive_dependent')
                if not allowed:valid=False;break
                roles[str(i)]=allowed
            elif pos in NOMINAL:
                if not any(compatible(c,case) or compatible(c,'Gen') for c,_,_ in readings):valid=False;break
        if valid:return dict(head_reading=[hc,hn,hg],roles=roles)
    return None


def pp_lattice(tokens,prep,domain,lexicon):
    result=[]
    for left,right in domain['boundaries']:
        if any(i!=prep and t['pos'] not in PHRASE for i,t in enumerate(tokens[left:right+1],left)):continue
        predicates=[p for p in domain['predicates'] if p is None or p<left or p>right]
        for head in domain['heads']:
            if not left<=head<=right:continue
            for case in ('Acc','Abl'):
                if role_witness(tokens,left,right,head,case,lexicon) is not None:result.extend([[left,right,head,case,p] for p in predicates])
    return result


def sv_morphology(sentences):
    lexicon={}
    for tokens in sentences:
        for t in tokens:
            if t['pos'] not in NOMINAL|{'VERB','AUX'}:continue
            fs=t['features'];person='3' if t['pos'] in ('NOUN','PROPN') else fs.get('Person','')
            reading=tuple((fs.get('Case',''),fs.get('Number',''),person,fs.get('VerbForm','')));lexicon.setdefault(readings_key(t),set()).add(reading)
    return {k:[list(r) for r in sorted(v)] for k,v in sorted(lexicon.items())}


def expand(value,allowed):
    return list(allowed) if not value else [v for v in value.split(',') if v in allowed]


def sv_domains(tokens,lexicon,hidden=False):
    subjects=[];predicates=[]
    for i,t in enumerate(tokens):
        for case,number,person,form in lexicon.get(readings_key(t),[]):
            if t['pos'] in NOMINAL and compatible(case,'Nom'):
                n='' if hidden else number;p=('3' if t['pos'] in ('NOUN','PROPN') else '') if hidden else person
                subjects.extend((i,nv,pv) for nv,pv in product(expand(n,('Sing','Plur')),expand(p,('1','2','3'))))
            elif t['pos'] in ('VERB','AUX') and form=='Fin':
                n='' if hidden else number;p='' if hidden else person
                predicates.extend((i,nv,pv) for nv,pv in product(expand(n,('Sing','Plur')),expand(p,('1','2','3'))))
    return dict(subjects=[list(x) for x in sorted(set(subjects))],predicates=[list(x) for x in sorted(set(predicates))])


def sv_lattice(domain,arm='agreement'):
    result=[]
    for s,sn,sp in domain['subjects']:
        for v,vn,vp in domain['predicates']:
            if s==v:continue
            if arm!='none' and sn!=vn:continue
            if arm in ('agreement','hidden') and sp!=vp:continue
            result.append([s,v,sn,sp,vn,vp])
    return result


def sv_value(candidate,field):
    return candidate[0] if field=='subject' else candidate[1] if field=='predicate' else tuple(candidate[2:4]) if field=='subject_features' else tuple(candidate[4:6])


def sv_interventions():return [tuple(c) for n in range(5) for c in combinations(SV_FIELDS,n)]


def sv_summary(candidates,reference,fields=()):
    survivors=[c for c in candidates if all(sv_value(c,f)==sv_value(reference,f) for f in fields)];pairs={tuple(c[:2]) for c in survivors};refpair=tuple(reference[:2]);choices={f:len({sv_value(c,f) for c in survivors}) for f in SV_FIELDS}
    return dict(remaining=len(survivors),links=len(pairs),reference_retained=list(reference) in survivors,reference_link_retained=refpair in pairs,unique_tuple_correct=len(survivors)==1 and survivors[0]==list(reference),unique_link_correct=len(pairs)==1 and refpair in pairs,false_unique_link=len(pairs)==1 and refpair not in pairs,choices=choices,
                unrevealed_resolved={f:choices[f]==1 and sv_value(survivors[0],f)==sv_value(reference,f) for f in SV_FIELDS if f not in fields})
