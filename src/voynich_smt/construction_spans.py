"""Local infinitive-construction interiors with complete token accounting.

Support is conditional evidence about a bounded fragment, not ownership entailment
or a complete clause parse. Unknown owners and unexplained external edges remain.
"""
from dataclasses import asdict
from functools import lru_cache
from .grammar_diagnostic import MorphAnalysis
from .relative_constituents import noun_phrases,OBJECT_ROOTS

PARTICLES=frozenset(('enim','autem','ergo','igitur'))
DATIVE_ROOTS=frozenset(('noc',))  # Explicit argument license: nocere + dative.


def decode(value):return MorphAnalysis(value['pos'],tuple(map(tuple,value['features'])))


def recognize(tokens,predicates,adapter,unit,*,strict=True,dative_frame=True,max_np=8):
    """Exact-cover DP over a fixed minimal construction interval.

    Anchors are its governor, infinitive(s), coordination terminals and any
    evidence nominals in the candidate. Every other token needs an adverb,
    discourse-particle or typed nominal-phrase role. No score or shortest-span
    preference is used. The one stored witness represents an existential result.
    """
    if unit['kind']=='shared_subject_participle':return {'status':'outside_grammar'}
    parent=unit['parent'];members=unit['members'];reads={int(p):decode(v) for p,v in unit['readings'].items()}
    anchors={parent:'governor',**{nf:'infinitive' for nf in members}}
    cue=unit.get('cue')
    if cue:
        for p in cue['marker_positions']:anchors[p]='coordinator'
        if cue['kind']=='paired_ne_c':
            for p in (members[0]-2,members[0]-1):anchors[p]='coordinator'
    sites=set(anchors)|set(reads);start=min(sites);end=max(sites)+1
    extra=[p for p in predicates if start<=p<end and p!=parent]
    result={'start':start,'end':end,'extra_finite':extra}
    if extra:return {**result,'status':'finite_barrier'}
    lexically_uncovered=[p for p in range(start,end) if p not in anchors and not adapter.analyze(tokens[p])]
    permitted=lambda p:any(r.pos in ('N','PRON','ADJ','NUM','PREP','ADV','VPAR') or
        r.pos=='CONJ' and (tokens[p] in PARTICLES or tokens[p] in ('et','uel','que')) for r in adapter.analyze(tokens[p]))
    pos_uncovered=[p for p in range(start,end) if p not in anchors and not permitted(p)]
    result.update(unknown_tokens=lexically_uncovered,pos_uncovered=pos_uncovered)
    if lexically_uncovered:return {**result,'status':'unknown_token'}
    if pos_uncovered:return {**result,'status':'unsupported_pos'}
    if not strict:return {**result,'status':'pos_supported'}
    lattice=[adapter.analyze(w) for w in tokens]
    pv=reads[parent]
    required={('embedded_subject',c['nonfinite']) for c in unit['parts'] if c['kind']=='perception_aci'}

    def roles(phrase):
        head=phrase['head'];noun=decode(phrase['analyses'][str(head)]);features=dict(noun.features)
        features.update(phrase['agreement']);bound=MorphAnalysis(noun.pos,tuple(sorted(features.items())))
        local_members=members
        if cue:
            boundary=min(cue['marker_positions'])
            local_members=[members[0]] if phrase['end']<=boundary else [members[1]]
        if phrase['argument_preposition'] is not None:
            return [('prepositional_oblique',nf,False) for nf in local_members]
        options=[];case=bound.get('Case')
        if case=='NOM':
            person='1' if tokens[head] in ('ego','nos') else '2' if tokens[head] in ('tu','uos','vos') else '3'
            if bound.get('Number')==pv.get('Number') and person==pv.get('Person'):
                options.append(('matrix_subject',parent,True))
        for c in unit['parts']:
            nf=c['nonfinite'];nr=reads[nf]
            if nf not in local_members:continue
            if case=='ACC':
                if c.get('embedded_subject')==head:options.append(('embedded_subject',nf,True))
                if nr.get('VerbKind')=='TRANS' or nr.get('VerbRoot') in OBJECT_ROOTS:options.append(('object',nf,True))
            if case=='DAT' and (nr.get('VerbKind')=='DAT' or dative_frame and nr.get('VerbRoot') in DATIVE_ROOTS):
                options.append(('dative_argument',nf,True))
            if case=='GEN' and nr.get('VerbKind')=='GEN':options.append(('genitive_argument',nf,True))
            if case=='ABL' and nr.get('VerbKind')=='ABL':options.append(('ablative_argument',nf,True))
        if case=='ABL' and pv.get('Voice')=='PASSIVE':options.append(('passive_instrument',parent,False))
        return options

    @lru_cache(None)
    def phrases(a,b):
        if any(p in anchors for p in range(a,b)):return ()
        values=[]
        for head in range(a,b):
            for noun in lattice[head]:
                if noun.pos not in ('N','PRON'):continue
                for phrase in noun_phrases(tokens,b,head,noun,adapter,radius=16):
                    if phrase['start']!=a:continue
                    if any(p in reads and decode(val)!=reads[p] for p,val in ((int(p),v) for p,v in phrase['analyses'].items())):continue
                    # The local NP grammar uses one head binding throughout.
                    values.append(phrase)
        return tuple(values)

    @lru_cache(None)
    def parse(pos,used):
        used=set(used)
        if pos==end:return () if required<=used else None
        if pos in anchors:
            tail=parse(pos+1,tuple(sorted(used)))
            return ({'positions':[pos],'role':anchors[pos],'reading':asdict(reads[pos]) if pos in reads else None},*tail) if tail is not None else None
        for reading in lattice[pos]:
            role='adverb' if reading.pos=='ADV' else 'particle' if tokens[pos] in PARTICLES and reading.pos=='CONJ' else None
            if role and (pos not in reads or reads[pos]==reading):
                tail=parse(pos+1,tuple(sorted(used)))
                if tail is not None:return ({'positions':[pos],'role':role,'reading':asdict(reading)},*tail)
        for stop in range(pos+1,min(end,pos+max_np)+1):
            for phrase in phrases(pos,stop):
                for role,target,unique in roles(phrase):
                    key=(role,target)
                    if unique and key in used:continue
                    tail=parse(stop,tuple(sorted(used|{key})))
                    if tail is not None:return ({'positions':list(range(pos,stop)),'role':role,'target':target,'phrase':phrase},*tail)
        return None

    witness=parse(start,())
    edge=lambda p:0<=p<len(tokens) and p not in predicates and any(r.pos in ('N','PRON','ADJ','NUM','VPAR') or r.pos=='V' and r.get('Mood')=='INF' for r in adapter.analyze(tokens[p]))
    result.update(open_nominal_or_nonfinite_edges=[p for p in (start-1,end) if edge(p)],
        unknown_edges=[p for p in (start-1,end) if 0<=p<len(tokens) and p not in predicates and not adapter.analyze(tokens[p])])
    if witness is None:return {**result,'status':'no_role_cover'}
    return {**result,'status':'supported','witness':list(witness)}


def analyze(tokens,predicates,adapter,serialized,dative_frame=True):
    """Parent sets under finite, lexical-POS and typed-interior screens."""
    results=[];parents={arm:{r['position']:set() for r in serialized['records']} for arm in ('finite','pos','typed')}
    for index,unit in enumerate(serialized['units']):
        if unit['kind']=='shared_subject_participle':continue
        pos=recognize(tokens,predicates,adapter,unit,strict=False)
        typed=recognize(tokens,predicates,adapter,unit,strict=True,dative_frame=dative_frame)
        finite=pos['status']!='finite_barrier'
        pos_ok=pos['status']=='pos_supported';typed_ok=typed['status']=='supported'
        assert not typed_ok or pos_ok
        for nf in unit['members']:
            if finite:parents['finite'][nf].add(unit['parent'])
            if pos_ok:parents['pos'][nf].add(unit['parent'])
            if typed_ok:parents['typed'][nf].add(unit['parent'])
        results.append({'unit':index,'finite_supported':finite,'pos':pos,'typed':typed})
    eligible={rec['position'] for rec in serialized['records'] if any(r.pos=='V' and r.get('Mood')=='INF' and r.get('Voice')=='ACTIVE' for r in adapter.analyze(tokens[rec['position']]))}
    return {'units':results,'parents':{arm:{str(nf):sorted(values) for nf,values in records.items() if nf in eligible} for arm,records in parents.items()},
        'firm_claims':[],'scope':'Conditional construction interiors only; unknown owner remains available.'}
