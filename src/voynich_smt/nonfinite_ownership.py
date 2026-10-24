"""Joint ownership of provisionally selected nonfinite predicates.

A bounded construction CSP, not a complete parse. One infinitive slot per simple
finite frame; unsupported coordination can cause explicit component abstention.
There is no fitted score, distance objective, or maximum-coverage objective.
"""
from dataclasses import asdict
from itertools import combinations
import z3
from .relative_constituents import MODAL_ROOTS,argument
from .relative_bridge import finite
from .grammar_diagnostic import MorphAnalysis

REPORT_ROOTS=frozenset(('cred','dic','fer'))
DOMAINS={'Gender':('M','F','N'),'Number':('S','P'),'Case':('NOM','ACC','GEN','DAT','ABL','VOC','LOC')}


def crosses(a,b,c,d):
    lo,hi=sorted((a,b));left,right=sorted((c,d))
    return lo<left<hi<right or left<lo<right<hi


def is_nonfinite(r):
    return (r.pos=='V' and r.get('Mood')=='INF' and r.get('Voice')=='ACTIVE' or
        r.pos=='VPAR' and r.get('Case')=='NOM' and r.get('Voice')=='ACTIVE')


def candidate_pool(tokens,predicates,adapter,*,scopes=(),boundaries=(),radius=32,reporting=True):
    lattice=[adapter.analyze(w) for w in tokens]
    selected={p for p in range(len(tokens)) if p not in predicates and any(is_nonfinite(r) for r in lattice[p])}
    segment=lambda p:sum(p>=b for b in boundaries)
    def exposed(a,b):
        lo,hi=sorted((a,b))
        return any(lo<p<hi and not any(lo<m<=p<=c<hi for m,c in scopes if m<c) for p in predicates)
    pool={p:[] for p in sorted(selected)}
    for nf in pool:
        for parent in predicates:
            if abs(nf-parent)>radius or segment(nf)!=segment(parent) or exposed(nf,parent):continue
            # A predicate before a relative marker cannot be an internal
            # dependent of that following relative's finite endpoint. Do not
            # treat the minimal interval's right edge as a complete clause end.
            if any(nf<m<=parent<=c or parent<m<=nf<=c for m,c in scopes if m<c):continue
            for nr in lattice[nf]:
                if not is_nonfinite(nr):continue
                for pr in lattice[parent]:
                    if not finite(pr):continue
                    if nr.pos=='V':
                        kind=('modal' if pr.get('VerbRoot') in MODAL_ROOTS and pr.get('Voice')=='ACTIVE' else
                            'passive_reporting' if reporting and pr.get('VerbRoot') in REPORT_ROOTS and pr.get('Voice')=='PASSIVE' else None)
                        if kind:
                            pool[nf].append(dict(nonfinite=nf,parent=parent,kind=kind,subject=None,
                                readings={nf:nr,parent:pr}))
                    else:
                        if nr.get('Number')!=pr.get('Number') or pr.get('Person')!='3':continue
                        for sub in range(max(0,nf-8),min(len(tokens),nf+9)):
                            if sub in predicates or sub in selected or segment(sub)!=segment(parent) or exposed(sub,parent):continue
                            for sr in lattice[sub]:
                                if (sr.pos in ('N','PRON') and sr.get('Case')=='NOM' and
                                        adapter.agrees(sr,nr,('Gender','Number')) and argument(sr,pr,tokens,sub,adapter)=='subject'):
                                    pool[nf].append(dict(nonfinite=nf,parent=parent,kind='shared_subject_participle',subject=sub,
                                        readings={nf:nr,parent:pr,sub:sr}))
    return pool


class Ownership:
    """Enumerate feasible owners through SAT queries, retaining all alternatives."""
    def __init__(self,tokens,predicates,adapter,*,scopes=(),boundaries=(),radius=32,capacity=True,noncrossing=True,reporting=True):
        self.tokens=tokens;self.predicates=predicates;self.adapter=adapter
        self.capacity=capacity;self.noncrossing=noncrossing
        self.pool=candidate_pool(tokens,predicates,adapter,scopes=scopes,boundaries=boundaries,radius=radius,reporting=reporting)
        # A participle can be an adjectival modifier, and an INF homograph can
        # have a nominal reading. Do not force those lexical alternatives into
        # finite ownership. Unambiguous infinitives with licensed frames remain
        # selected; unsupported ones explicitly abstain.
        self.alternatives={nf:[r for r in adapter.analyze(tokens[nf]) if not finite(r) and not (r.pos=='V' and r.get('Mood')=='INF')] for nf in self.pool}
        # Connect every pair that can interact through readings, capacity or
        # crossing arcs; contradictory unrelated components do not poison others.
        groups=[{p} for p in self.pool]
        for a,b in combinations(self.pool,2):
            left=self.pool[a];right=self.pool[b]
            dependent=any(set(x['readings']) & set(y['readings']) or
                (noncrossing and crosses(a,x['parent'],b,y['parent'])) for x in left for y in right)
            if dependent:
                ga=next(g for g in groups if a in g);gb=next(g for g in groups if b in g)
                if ga is not gb:ga.update(gb);groups.remove(gb)
        self.components=[];self.component_for={};self.queries=0
        for group in sorted(groups,key=lambda g:min(g)):
            component=self._component(sorted(group));index=len(self.components);self.components.append(component)
            for nf in group:self.component_for[nf]=index
        self.records=[]
        for nf,choices in self.pool.items():
            comp=self.components[self.component_for[nf]]
            possible=sorted({c['parent'] for j,c in enumerate(choices) if comp['sat'] and self._query(comp,comp['choice'][nf]==j)})
            nearest=self.nearest(nf)
            unresolved=comp['sat'] and self._query(comp,comp['choice'][nf]==-1)
            self.records.append({'position':nf,'component':self.component_for[nf],
                'candidate_parents':sorted({c['parent'] for c in choices}),
                'possible_parents':possible,'nearest_parents':nearest,'unresolved_possible':unresolved,
                'selection_optional':bool(self.alternatives[nf]),
                'status':'unlicensed' if not choices else 'conflict' if not comp['sat'] else 'optional' if len(possible)==1 and unresolved else 'unique' if len(possible)==1 else 'ambiguous' if possible else 'unresolved'})

    def _component(self,group):
        solver=z3.Solver();choice={};readings={};features={}
        sites=sorted({p for nf in group for c in self.pool[nf] for p in c['readings']})
        lattice={p:self.adapter.analyze(self.tokens[p]) for p in sites}
        for p in sites:
            readings[p]=z3.Int(f'r_{p}')
            solver.add(readings[p]>=0,readings[p]<len(lattice[p]))
            for key,domain in DOMAINS.items():
                var=z3.Int(f'{key}_{p}');features[p,key]=var
                solver.add(var>=0,var<len(domain))
                for i,r in enumerate(lattice[p]):
                    value=r.get(key)
                    allowed=({'M','F'} if key=='Gender' and value=='C' else set(domain) if value in (None,'X','0') else {value})
                    solver.add(z3.Implies(readings[p]==i,z3.Or([var==domain.index(v) for v in allowed if v in domain])))
        for nf in group:
            choices=self.pool[nf];choice[nf]=z3.Int(f'owner_choice_{nf}')
            if not choices:solver.add(choice[nf]==-1);continue
            solver.add(choice[nf]>=(-1 if self.alternatives[nf] else 0),choice[nf]<len(choices))
            if self.alternatives[nf]:
                solver.add(z3.Implies(choice[nf]==-1,z3.Or([readings[nf]==lattice[nf].index(r) for r in self.alternatives[nf]])))
            for j,c in enumerate(choices):
                conditions=[readings[p]==lattice[p].index(r) for p,r in c['readings'].items()]
                if c['subject'] is not None:
                    conditions.extend(features[nf,k]==features[c['subject'],k] for k in ('Gender','Number'))
                    conditions.append(features[nf,'Number']==features[c['parent'],'Number'])
                solver.add(z3.Implies(choice[nf]==j,z3.And(conditions)))
        for a,b in combinations(group,2):
            for i,x in enumerate(self.pool[a]):
                for j,y in enumerate(self.pool[b]):
                    overloaded=(self.capacity and x['parent']==y['parent'] and x['kind']!='shared_subject_participle' and y['kind']!='shared_subject_participle')
                    if overloaded or (self.noncrossing and crosses(a,x['parent'],b,y['parent'])):
                        solver.add(z3.Not(z3.And(choice[a]==i,choice[b]==j)))
        result=solver.check();self.queries+=1
        if result not in (z3.sat,z3.unsat):raise RuntimeError('Ownership solver returned unknown')
        return dict(group=group,solver=solver,choice=choice,readings=readings,features=features,lattice=lattice,sat=result==z3.sat)

    def _query(self,comp,condition):
        solver=comp['solver'];solver.push();solver.add(condition);answer=solver.check();solver.pop();self.queries+=1
        if answer not in (z3.sat,z3.unsat):raise RuntimeError('Ownership solver returned unknown')
        return answer==z3.sat

    def nearest(self,nf):
        parents=sorted({c['parent'] for c in self.pool.get(nf,[])})
        return [p for p in parents if abs(p-nf)==min(abs(q-nf) for q in parents)] if parents else []

    def _bindings(self,comp,w,marker,child):
        assigned={};conditions=[]
        def add(p,value):
            r=MorphAnalysis(value['pos'],tuple(map(tuple,value['features'])))
            if p in assigned and assigned[p]!=r:conditions.append(z3.BoolVal(False))
            assigned[p]=r
        for p,value in w['phrase']['analyses'].items():add(int(p),value)
        for p,key in [(w['antecedent'],'noun'),(marker,'pronoun'),(child,'child_verb'),(w['parent'],'parent_verb'),(w['via'],'nonfinite_verb')]:
            if p is not None:add(p,w[key])
        if w['subject'] is not None:add(w['subject'],w['subject_reading'])
        for p,r in assigned.items():
            if p in comp['readings']:
                if r not in comp['lattice'][p]:conditions.append(z3.BoolVal(False))
                else:conditions.append(comp['readings'][p]==comp['lattice'][p].index(r))
        # Add the relative witness's own feature unifications even when a site
        # is not otherwise involved in the ownership component.
        allfeatures=dict(comp['features'])
        for p,r in assigned.items():
            for key,domain in DOMAINS.items():
                if (p,key) not in allfeatures:
                    var=z3.Int(f'bridge_{key}_{p}');allfeatures[p,key]=var
                    value=r.get(key)
                    allowed=({'M','F'} if key=='Gender' and value=='C' else set(domain) if value in (None,'X','0') else {value})
                    conditions.append(z3.Or([var==domain.index(v) for v in allowed if v in domain]))
        head=w['antecedent'];via=w['via']
        conditions.extend(allfeatures[head,k]==allfeatures[marker,k] for k in ('Gender','Number'))
        for p in w['phrase']['analyses']:
            p=int(p)
            if assigned[p].pos in ('ADJ','NUM','PRON','VPAR'):
                conditions.extend(allfeatures[head,k]==allfeatures[p,k] for k in DOMAINS)
        for k,value in w['phrase'].get('agreement',{}).items():conditions.append(allfeatures[head,k]==DOMAINS[k].index(value))
        if w['subject'] is not None:
            conditions.extend(allfeatures[via,k]==allfeatures[w['subject'],k] for k in ('Gender','Number'))
        return z3.And(conditions)

    def assess(self,w,marker,child,*,nearest=False):
        nf=w['via'];parent=w['parent']
        if nf not in self.component_for or not self.pool[nf]:return 'unlicensed'
        if nearest:
            compatible=[]
            for c in self.pool[nf]:
                if c['parent']!=parent or c['subject']!=w['subject']:continue
                if all(c['readings'][p]==MorphAnalysis(value['pos'],tuple(map(tuple,value['features']))) for p,value in ((nf,w['nonfinite_verb']),(parent,w['parent_verb']))):
                    compatible.append(c)
            if not compatible:return 'excluded'
            choices=self.nearest(nf)
            return 'entailed' if choices==[parent] else 'ambiguous' if parent in choices else 'excluded'
        comp=self.components[self.component_for[nf]]
        if not comp['sat']:return 'conflict'
        options=self.pool[nf];eq=z3.Or([comp['choice'][nf]==j for j,c in enumerate(options) if c['parent']==parent])
        bindings=z3.And(self._bindings(comp,w,marker,child),comp['choice'][nf]>=0)
        if not self._query(comp,z3.And(bindings,eq)):return 'excluded'
        return 'ambiguous' if self._query(comp,z3.And(bindings,z3.Not(eq))) else 'entailed'

    def serializable(self):
        return {'records':self.records,'components':[{'positions':c['group'],'satisfiable':c['sat']} for c in self.components],
            'candidates':{str(nf):[{**{k:v for k,v in c.items() if k!='readings'},'readings':{str(p):asdict(r) for p,r in c['readings'].items()}} for c in choices] for nf,choices in self.pool.items()}}


def filter_bridges(result,ownership,marker,child,*,nearest=False):
    chains=[];rejected=[]
    for w in result['chains']:
        status='direct' if w['via'] is None else ownership.assess(w,marker,child,nearest=nearest)
        value={**w,'ownership':status}
        (chains if status in ('direct','entailed','ambiguous') else rejected).append(value)
    signatures={(w['antecedent'],w['via'],w['parent']) for w in chains}
    status=('unique_chain' if len(signatures)==1 and all(w['ownership']!='ambiguous' for w in chains) else
        'ownership_ambiguous' if len(signatures)==1 else 'ambiguous' if chains else
        result['status'] if not result['chains'] else 'no_bridge')
    return {'status':status,'parents':sorted({w['parent'] for w in chains}),
        'antecedents':sorted({w['antecedent'] for w in chains}),'chains':chains,'rejected':rejected}
