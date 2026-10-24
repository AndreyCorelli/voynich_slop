"""Bounded argument structures with explicit agreeing ablative participial clauses.

This diagnostic enumerates conditional analyses of a frozen unit's interior.
It does not resolve lexical adjunct attachment or assert complete clause coverage.
"""
from functools import lru_cache
from dataclasses import asdict
import json
from .construction_spans import recognize as old_recognize,decode,PARTICLES,DATIVE_ROOTS
from .relative_constituents import noun_phrases,OBJECT_ROOTS


def recognize(tokens,predicates,adapter,unit,*,coordination=True,attachment=True,perdere_frame=False,participles=True,nisi_clause=False,limit=256):
    gate=old_recognize(tokens,predicates,adapter,unit,strict=False)
    if gate['status']=='unsupported_pos' and nisi_clause and all(tokens[p]=='nisi' and any(r.pos in ('ADV','CONJ') for r in adapter.analyze(tokens[p])) for p in gate['pos_uncovered']):
        gate={**gate,'status':'pos_supported','pos_uncovered':[]}
    if gate['status']!='pos_supported':return gate
    start,end=gate['start'],gate['end'];members=unit['members'];parent=unit['parent'];cue=unit.get('cue')
    reads={int(p):decode(r) for p,r in unit['readings'].items()}
    anchors={parent:'governor',**{n:'infinitive' for n in members}}
    if cue:
        anchors.update({p:'coordinator' for p in cue['marker_positions']})
        if cue['kind']=='paired_ne_c':anchors.update({p:'coordinator' for p in (members[0]-2,members[0]-1)})
    lattice=[adapter.analyze(w) for w in tokens]
    object_roots=OBJECT_ROOTS | ({'perd'} if perdere_frame else set())
    required={('embedded_subject',p['nonfinite']) for p in unit['parts'] if p['kind']=='perception_aci'}

    @lru_cache(None)
    def phrases(a,b):
        if any(p in anchors for p in range(a,b)):return ()
        values=[]
        for h in range(a,b):
            for n in lattice[h]:
                if n.pos not in ('N','PRON'):continue
                for phrase in noun_phrases(tokens,b,h,n,adapter,radius=16):
                    if phrase['start']!=a:continue
                    if any(int(p) in reads and decode(v)!=reads[int(p)] for p,v in phrase['analyses'].items()):continue
                    values.append(phrase)
        return tuple(values)

    def targets(a,b):
        if not cue:return [(members[0],)]
        split=min(cue['marker_positions'])
        local=members[0] if b<=split else members[1]
        if attachment and (b<=min(members) or a>max(members)):
            return [(m,) for m in members]+[tuple(members)]
        return [(local,)]

    def role_options(phrase):
        head=phrase['head'];n=decode(phrase['analyses'][str(head)]);case=n.get('Case');a,b=phrase['start'],phrase['end']
        if phrase['argument_preposition'] is not None:
            return [('prepositional_oblique',t,False) for t in targets(a,b)]
        roles=[]
        if case=='NOM':
            person='1' if tokens[head] in ('ego','nos') else '2' if tokens[head] in ('tu','uos','vos') else '3'
            if phrase['agreement']['Number']==reads[parent].get('Number') and person==reads[parent].get('Person'):
                roles.append(('matrix_subject',(parent,),True))
        for ts in targets(a,b):
            if case=='ACC' and all(reads[nf].get('VerbKind')=='TRANS' or reads[nf].get('VerbRoot') in object_roots for nf in ts):
                roles.append(('object',ts,True))
            if case=='DAT' and all(reads[nf].get('VerbKind')=='DAT' or reads[nf].get('VerbRoot') in DATIVE_ROOTS for nf in ts):
                roles.append(('dative_argument',ts,True))
            for label,kind in [('genitive_argument','GEN'),('ablative_argument','ABL')]:
                if case==kind and all(reads[nf].get('VerbKind')==kind for nf in ts):roles.append((label,ts,True))
        if case=='ACC':
            for part in unit['parts']:
                if part.get('embedded_subject')==head:roles.append(('embedded_subject',(part['nonfinite'],),True))
        if case=='ABL':
            if attachment:
                # Case licenses an unresolved oblique, not an instrument or a
                # material/absolute construction. Preserve both attachment sites.
                roles.extend(('unresolved_ablative',(p,),False) for p in [parent]+members)
            elif reads[parent].get('Voice')=='PASSIVE':roles.append(('passive_instrument',(parent,),False))
        return roles

    @lru_cache(None)
    def segments(a):
        values=[]
        if a in anchors:
            return ((a+1,{'positions':[a],'role':anchors[a],'reading':asdict(reads[a]) if a in reads else None},()),)
        for r in lattice[a]:
            role='adverb' if r.pos=='ADV' else 'particle' if tokens[a] in PARTICLES and r.pos=='CONJ' else None
            if role and (a not in reads or r==reads[a]):values.append((a+1,{'positions':[a],'role':role,'reading':asdict(r)},()))
        for b in range(a+1,min(end,a+8)+1):
            for phrase in phrases(a,b):
                for role,ts,unique in role_options(phrase):
                    values.append((b,{'positions':list(range(a,b)),'role':role,'targets':list(ts),'phrases':[phrase],'markers':[]},tuple((role,t) for t in ts) if unique else ()))
        if participles:
            # Minimal two-token clause, either N VPAR or VPAR N. A separately
            # enabled nisi marker belongs to this clause, never a noun modifier.
            first=a+1 if nisi_clause and tokens[a]=='nisi' and any(r.pos in ('ADV','CONJ') for r in lattice[a]) else a
            stop=first+2
            if stop<=end and not any(p in anchors for p in range(a,stop)):
                for subject,part in ((first,first+1),(first+1,first)):
                    for noun in lattice[subject]:
                        if noun.pos not in ('N','PRON') or noun.get('Case')!='ABL':continue
                        for verbal in lattice[part]:
                            if verbal.pos!='VPAR' or verbal.get('Case')!='ABL':continue
                            if not adapter.agrees(noun,verbal,('Case','Number','Gender')):continue
                            if any(p in reads and reads[p]!=r for p,r in ((subject,noun),(part,verbal))):continue
                            # Bind all agreement features jointly, including X/C.
                            def choices(r,key):
                                value=r.get(key)
                                return {'S','P'} if key=='Number' and value in (None,'X','0') else {'M','F','N'} if value in (None,'X','0') else {'M','F'} if key=='Gender' and value=='C' else {value}
                            numbers=choices(noun,'Number')&choices(verbal,'Number')
                            genders=choices(noun,'Gender')&choices(verbal,'Gender')
                            if not numbers or not genders:continue
                            for target in [parent]+members:
                                marker_reading=next((r for r in lattice[a] if r.pos in ('ADV','CONJ')),None) if first!=a else None
                                clause={'subject':subject,'participle':part,'marker':a if first!=a else None,
                                    'analyses':{str(subject):asdict(noun),str(part):asdict(verbal)},
                                    'marker_reading':asdict(marker_reading) if marker_reading else None,
                                    'agreement':{'Case':'ABL','Gender':sorted(genders)[0],'Number':sorted(numbers)[0]}}
                                values.append((stop,{'positions':list(range(a,stop)),'role':'ablative_participial_clause',
                                    'targets':[target],'clause':clause},()))
        if coordination:
            # Two nominal conjuncts, optionally correlative et ... et ... .
            first=a+1 if tokens[a]=='et' and any(r.pos=='CONJ' for r in lattice[a]) else a
            for marker in range(first+1,min(end,a+9)):
                if marker in anchors or tokens[marker] not in ('et','uel'):continue
                if not any(r.pos=='CONJ' for r in lattice[marker]):continue
                for b in range(marker+2,min(end,a+12)+1):
                    for p in phrases(first,marker):
                        for q in phrases(marker+1,b):
                            if any(decode(x['analyses'][str(x['head'])]).get('Case')!='ACC' or x['argument_preposition'] is not None for x in (p,q)):continue
                            for ts in targets(a,b):
                                if not all(reads[nf].get('VerbKind')=='TRANS' or reads[nf].get('VerbRoot') in object_roots for nf in ts):continue
                                markers=([a] if first!=a else [])+[marker]
                                values.append((b,{'positions':list(range(a,b)),'role':'object','targets':list(ts),'phrases':[p,q],'markers':markers},tuple(('object',t) for t in ts)))
        return tuple(values)

    structures={};overflow=False
    def visit(pos,used,witness):
        nonlocal overflow
        if overflow:return
        if pos==end:
            if not required<=used:return
            links=[];groups=[]
            for segment in witness:
                if 'clause' in segment:
                    clause=segment['clause'];part=clause['participle'];ts=tuple(segment['targets'])
                    groups.append(('ablative_participial_clause',(part,),ts))
                    links.append((clause['subject'],part,'participial_subject'))
                    links.extend((part,t,'participial_adjunct') for t in ts)
                    if clause['marker'] is not None:links.append((clause['marker'],part,'clause_marker'))
                    continue
                if 'phrases' not in segment:continue
                heads=tuple(p['head'] for p in segment['phrases']);ts=tuple(segment['targets']);role=segment['role']
                groups.append((role,heads,ts))
                links.extend((h,t,role) for h in heads for t in ts)
            # Keep clausal internal dependencies in the signature; unlike NP
            # modifiers, these are precisely the distinctions under diagnosis.
            signature=(tuple(sorted(groups)),tuple(sorted(links)))
            if signature not in structures:
                if len(structures)>=limit:overflow=True;return
                structures[signature]={'groups':[{'role':r,'heads':list(h),'targets':list(t)} for r,h,t in signature[0]],
                    'links':[list(l) for l in sorted(links)],'witness':list(witness)}
            return
        for stop,segment,slots in segments(pos):
            if set(slots)&used:continue
            # No unmarked adjacent double-object construction is declared.
            if witness and witness[-1]['role']=='object' and segment['role']=='object':continue
            visit(stop,used|set(slots),witness+[segment])
    visit(start,set(),[])
    return {**gate,'status':'truncated' if overflow else 'supported' if structures else 'no_role_cover',
        'structures':list(structures.values()),'complete_enumeration':not overflow,
        'attachment_status':'unresolved' if overflow or len(structures)!=1 or any(g['role'] in ('unresolved_ablative','ablative_participial_clause') for s in structures.values() for g in s['groups']) else 'unique_within_grammar',
        'scope':'Fixed interior only; unknown owner and external arguments remain unmodeled.'}
