"""Open-owner complement coverage and optional two-infinitive units.

A construction diagnostic, not a complete Latin parse. Every NF can retain an
unknown owner. Consequently lexical candidate uniqueness is never entailment.
"""
from dataclasses import asdict
from itertools import combinations,product
import z3
from .nonfinite_ownership import candidate_pool,crosses,DOMAINS
from .relative_bridge import finite


def locality(a,b,predicates,scopes,boundaries,radius=32):
    lo,hi=sorted((a,b))
    return (hi-lo<=radius and sum(a>=x for x in boundaries)==sum(b>=x for x in boundaries)
        and not any(lo<f<hi and not any(lo<m<=f<=c<hi for m,c in scopes if m<c) for f in predicates)
        and not any(a<m<=b<=c or b<m<=a<=c for m,c in scopes if m<c))


def expanded_pool(tokens,predicates,adapter,scopes=(),boundaries=(),expanded=True):
    pool=candidate_pool(tokens,predicates,adapter,scopes=scopes,boundaries=boundaries)
    if not expanded:return pool
    lattice=[adapter.analyze(w) for w in tokens]
    for nf in pool:
        for parent in predicates:
            if not locality(nf,parent,predicates,scopes,boundaries):continue
            for nr,pr in product(lattice[nf],lattice[parent]):
                if nr.pos!='V' or nr.get('Mood')!='INF' or nr.get('Voice')!='ACTIVE' or not finite(pr) or pr.get('Voice')!='ACTIVE':continue
                root=pr.get('VerbRoot')
                kind=('negative_imperative' if root=='nol' and pr.get('Mood')=='IMP' and pr.get('Person')=='2' else
                    'habitual' if root=='sol' else 'perception_aci' if root=='uid' else None)
                if kind is None:continue
                evidence=[None]
                if kind=='perception_aci':
                    # A bounded explicit accusative embedded-subject hypothesis.
                    # This does not distinguish that subject from an INF object.
                    evidence=[(p,r) for p in range(min(nf,parent)+1,max(nf,parent)) if abs(p-nf)<=3 and p not in predicates and p not in pool
                        for r in lattice[p] if r.pos in ('N','PRON') and r.get('Case')=='ACC']
                for subject in evidence:
                    readings={nf:nr,parent:pr}
                    if subject:readings[subject[0]]=subject[1]
                    pool[nf].append({'nonfinite':nf,'parent':parent,'kind':kind,'subject':None,
                        'embedded_subject':subject[0] if subject else None,'readings':readings})
    return pool


def coordination_cues(tokens,predicates,pool,adapter,boundaries=(),gap=8):
    infinitives=[nf for nf in pool if any(r.pos=='V' and r.get('Mood')=='INF' and r.get('Voice')=='ACTIVE' for r in adapter.analyze(tokens[nf]))]
    cues=[]
    for a,b in zip(infinitives,infinitives[1:]):
        if b-a>gap or any(a<f<b for f in predicates) or any(a<end<=b for end in boundaries):continue
        for m in range(a+1,b):
            if tokens[m] in ('et','aut','uel','nec','neque'):
                readings=[r for r in adapter.analyze(tokens[m]) if r.pos=='CONJ']
                if not readings:continue
                positions=[m];kind='conjunction';chosen={m:readings[0]}
            elif (tokens[m:m+2]==['ne','c'] and m+2==b and a>=2 and tokens[a-2:a]==['ne','c']):
                positions=[m,m+1];kind='paired_ne_c';chosen={}
            else:continue
            # Remaining material can be nominal/adverbial arguments or modifiers;
            # another connective or unknown token blocks this narrow flat unit.
            if any(not any(r.pos in ('N','PRON','ADJ','NUM','PREP','ADV','VPAR') for r in adapter.analyze(tokens[p]))
                    for p in range(a+1,b) if p not in positions):continue
            cues.append({'members':[a,b],'marker_positions':positions,'kind':kind,'readings':chosen})
    return cues


def merge_readings(*maps):
    merged={}
    for mapping in maps:
        for p,r in mapping.items():
            if p in merged and merged[p]!=r:return None
            merged[p]=r
    return merged


class ComplementModel:
    def __init__(self,tokens,predicates,adapter,*,scopes=(),boundaries=(),expanded=True,coordination=True):
        self.tokens=tokens;self.predicates=predicates;self.adapter=adapter
        self.pool=expanded_pool(tokens,predicates,adapter,scopes,boundaries,expanded)
        self.cues=coordination_cues(tokens,predicates,self.pool,adapter,boundaries) if coordination else []
        self.units=[]
        for nf,choices in self.pool.items():
            for c in choices:self.units.append({'members':[nf],'parent':c['parent'],'kind':c['kind'],'readings':c['readings'],'parts':[c],'cue':None})
        for cue in self.cues:
            a,b=cue['members']
            for x,y in product(self.pool[a],self.pool[b]):
                if x['kind']=='shared_subject_participle' or y['kind']=='shared_subject_participle' or x['parent']!=y['parent']:continue
                readings=merge_readings(x['readings'],y['readings'],cue['readings'])
                if readings is None:continue
                self.units.append({'members':[a,b],'parent':x['parent'],'kind':'coordinated_infinitives',
                    'readings':readings,'parts':[x,y],'cue':cue})
        self.solver=z3.Solver();self.selected=[z3.Bool(f'unit_{i}') for i in range(len(self.units))]
        self.unknown={nf:z3.Bool(f'unknown_{nf}') for nf in self.pool};self.read={};self.features={};self.queries=0
        sites=sorted({p for u in self.units for p in u['readings']})
        for p in sites:
            lattice=adapter.analyze(tokens[p]);self.read[p]=z3.Int(f'reading_{p}')
            self.solver.add(self.read[p]>=0,self.read[p]<len(lattice))
            for key,domain in DOMAINS.items():
                var=z3.Int(f'{key}_{p}');self.features[p,key]=var
                for j,r in enumerate(lattice):
                    value=r.get(key);values=('M','F') if key=='Gender' and value=='C' else domain if value in (None,'X','0') else (value,)
                    self.solver.add(z3.Implies(self.read[p]==j,z3.Or([var==domain.index(v) for v in values if v in domain])))
        for nf in self.pool:
            cover=[self.selected[i] for i,u in enumerate(self.units) if nf in u['members']]
            self.solver.add(z3.PbEq([(b,1) for b in (*cover,self.unknown[nf])],1))
        for i,u in enumerate(self.units):
            conditions=[self.read[p]==adapter.analyze(tokens[p]).index(r) for p,r in u['readings'].items()]
            for c in u['parts']:
                if c['subject'] is not None:
                    conditions.extend(self.features[c['nonfinite'],k]==self.features[c['subject'],k] for k in ('Gender','Number'))
            self.solver.add(z3.Implies(self.selected[i],z3.And(conditions)))
        # One complement UNIT per finite frame. Participial adjuncts do not
        # consume that slot. Overlapping units cannot both cover the same NF.
        slots={}
        for i,u in enumerate(self.units):
            if u['kind']!='shared_subject_participle':slots.setdefault(u['parent'],[]).append(self.selected[i])
        for choices in slots.values():self.solver.add(z3.PbLe([(b,1) for b in choices],1))
        for i,j in combinations(range(len(self.units)),2):
            x,y=self.units[i],self.units[j]
            if any(crosses(a,x['parent'],b,y['parent']) for a in x['members'] for b in y['members']):
                self.solver.add(z3.Not(z3.And(self.selected[i],self.selected[j])))
        assert self.query(*self.unknown.values())

    def query(self,*conditions):
        self.solver.push();self.solver.add(*conditions);result=self.solver.check();self.solver.pop();self.queries+=1
        if result not in (z3.sat,z3.unsat):raise RuntimeError('Unknown complement satisfiability')
        return result==z3.sat

    def owner(self,nf,parent):return z3.Or([self.selected[i] for i,u in enumerate(self.units) if nf in u['members'] and u['parent']==parent])
    def possible(self,nf):
        return [parent for parent in sorted({c['parent'] for c in self.pool[nf]}) if self.query(self.owner(nf,parent))]
    def can_assign(self,requirements):return self.query(*[self.owner(nf,parent) for nf,parent in requirements])

    def serializable(self):
        def choice(c):return {**{k:v for k,v in c.items() if k!='readings'},'readings':{str(p):asdict(r) for p,r in c['readings'].items()}}
        records=[]
        for nf in self.pool:
            parents=self.possible(nf)
            records.append({'position':nf,'candidate_parents':sorted({c['parent'] for c in self.pool[nf]}),
                'possible_parents':parents,'unknown_possible':self.query(self.unknown[nf]),
                'conditional_unique':len(parents)==1,'firm_owner':None})
        return {'records':records,'candidates':{str(nf):[choice(c) for c in values] for nf,values in self.pool.items()},
            'cues':[choice(c) for c in self.cues],
            'units':[{**{k:v for k,v in u.items() if k not in ('readings','parts','cue')},
                'readings':{str(p):asdict(r) for p,r in u['readings'].items()},'parts':[choice(c) for c in u['parts']],
                'cue':choice(u['cue']) if u['cue'] is not None else None} for u in self.units]}
