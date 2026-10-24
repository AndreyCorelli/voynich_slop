"""Replay plus independently encoded Boolean ownership CSPs.

The primary implementation uses integer option/reading variables and pairwise
capacity constraints. This checker uses Boolean options/readings and slot
cardinality, and independently checks lexical and structural licenses.
"""
from collections import Counter
from dataclasses import asdict
import hashlib
from itertools import combinations
from pathlib import Path
import z3
from voynich_smt.grammar_diagnostic import MorphAnalysis
from voynich_smt.nonfinite_ownership import Ownership,filter_bridges
from benchmarks.grammar_relative_constituents_iteration15_validate import FrozenAdapter,normalized,check_witness
from benchmarks.grammar_nonfinite_ownership_iteration16 import OUT,NINE,TEN,FIFTEEN,RESERVE,ARMS,load,save
from benchmarks.grammar_nonfinite_ownership_iteration16_evaluate import ownership_truth,ownership_metrics,relative_metrics,reference_paths

DOMAINS={'Gender':('M','F','N'),'Number':('S','P'),'Case':('NOM','ACC','GEN','DAT','ABL','VOC','LOC')}
def reading(value):return MorphAnalysis(value['pos'],tuple(map(tuple,value['features'])))
def finite(r):return r.pos=='V' and r.get('Mood') in ('IND','SUB','IMP')
def alternatives(adapter,word):return [r for r in adapter.analyze(word) if not finite(r) and not (r.pos=='V' and r.get('Mood')=='INF')]
def crossing(a,b,c,d):
    x,y=sorted((a,b));u,v=sorted((c,d))
    return x<u<y<v or u<x<v<y


class Independent:
    def __init__(self,tokens,predicates,adapter,scopes,bounds,options,serialized,group,unknown_owner=False):
        self.tokens=tokens;self.adapter=adapter;self.options=options;self.group=group
        self.pool={nf:serialized['candidates'][str(nf)] for nf in group}
        self.solver=z3.Solver();self.rb={};self.f={};self.select={};self.null={};self.queries=0
        proposed={r['position'] for r in serialized['records']}
        for nf in group:
            self.site(nf)
            alts=alternatives(adapter,tokens[nf]);choices=[]
            self.null[nf]=z3.Bool(f'null_{nf}')
            for j,c in enumerate(self.pool[nf]):
                self.validate_candidate(c,predicates,scopes,bounds,proposed)
                selected=z3.Bool(f'option_{nf}_{j}');self.select[nf,j]=selected;choices.append(selected)
                constraints=[]
                for p,val in c['readings'].items():
                    p=int(p);self.site(p);r=reading(val)
                    constraints.append(self.rb[p][adapter.analyze(tokens[p]).index(r)])
                if c['subject'] is not None:
                    for key in ('Gender','Number'):constraints.append(self.f[nf,key]==self.f[c['subject'],key])
                    constraints.append(self.f[nf,'Number']==self.f[c['parent'],'Number'])
                self.solver.add(z3.Implies(selected,z3.And(constraints)))
            if not self.pool[nf]:self.solver.add(self.null[nf])
            elif unknown_owner:pass
            elif alts:
                self.solver.add(z3.Implies(self.null[nf],z3.Or([self.rb[nf][adapter.analyze(tokens[nf]).index(r)] for r in alts])))
            else:self.solver.add(z3.Not(self.null[nf]))
            self.solver.add(z3.PbEq([(b,1) for b in (*choices,self.null[nf])],1))
        if options['capacity']:
            slots={}
            for nf in group:
                for j,c in enumerate(self.pool[nf]):
                    if c['kind']!='shared_subject_participle':slots.setdefault(c['parent'],[]).append(self.select[nf,j])
            for values in slots.values():self.solver.add(z3.PbLe([(b,1) for b in values],1))
        if options['noncrossing']:
            for a,b in combinations(group,2):
                for i,x in enumerate(self.pool[a]):
                    for j,y in enumerate(self.pool[b]):
                        if crossing(a,x['parent'],b,y['parent']):self.solver.add(z3.Not(z3.And(self.select[a,i],self.select[b,j])))

    def site(self,p):
        if p in self.rb:return
        readings=self.adapter.analyze(self.tokens[p]);self.rb[p]=[z3.Bool(f'lex_{p}_{i}') for i in range(len(readings))]
        self.solver.add(z3.PbEq([(b,1) for b in self.rb[p]],1))
        for key,domain in DOMAINS.items():
            var=z3.String(f'{key}_{p}');self.f[p,key]=var
            for i,r in enumerate(readings):
                value=r.get(key)
                values=('M','F') if key=='Gender' and value=='C' else domain if value in (None,'X','0') else (value,)
                self.solver.add(z3.Implies(self.rb[p][i],z3.Or([var==v for v in values if v in domain])))

    def validate_candidate(self,c,predicates,scopes,bounds,proposed):
        nf=c['nonfinite'];parent=c['parent'];read={int(p):reading(r) for p,r in c['readings'].items()}
        for p,r in read.items():assert r in self.adapter.analyze(self.tokens[p])
        nr,pr=read[nf],read[parent]
        assert nf not in predicates and parent in predicates and finite(pr) and abs(nf-parent)<=32
        segment=lambda p:sum(p>=b for b in bounds)
        assert segment(nf)==segment(parent)
        def exposed(a,b):
            low,high=sorted((a,b))
            return any(low<f<high and not any(low<m<=f<=target<high for m,target in scopes if m<target) for f in predicates)
        assert not exposed(nf,parent)
        assert not any(nf<m<=parent<=target or parent<m<=nf<=target for m,target in scopes if m<target)
        if c['kind']=='shared_subject_participle':
            sub=c['subject'];sr=read[sub]
            assert nr.pos=='VPAR' and nr.get('Case')=='NOM' and nr.get('Voice')=='ACTIVE'
            assert nr.get('Number')==pr.get('Number') and pr.get('Person')=='3'
            assert sub not in predicates and sub not in proposed and abs(sub-nf)<=8
            assert segment(sub)==segment(parent) and not exposed(sub,parent)
            assert sr.pos in ('N','PRON') and sr.get('Case')=='NOM' and sr.get('Number')==pr.get('Number')
            assert self.adapter.agrees(sr,nr,('Gender','Number'))
            assert self.tokens[sub] not in ('ego','nos','tu','uos','vos')
        else:
            assert c['subject'] is None and nr.pos=='V' and nr.get('Mood')=='INF' and nr.get('Voice')=='ACTIVE'
            if c['kind']=='modal':assert pr.get('VerbRoot') in ('deb','poss') and pr.get('Voice')=='ACTIVE'
            else:
                assert c['kind']=='passive_reporting' and self.options['reporting']
                assert pr.get('VerbRoot') in ('cred','dic','fer') and pr.get('Voice')=='PASSIVE'

    def query(self,*conditions):
        self.solver.push();self.solver.add(*conditions);answer=self.solver.check();self.solver.pop();self.queries+=1
        assert answer in (z3.sat,z3.unsat)
        return answer==z3.sat

    def owner(self,nf,parent):return z3.Or([self.select[nf,j] for j,c in enumerate(self.pool[nf]) if c['parent']==parent])

    def bind_witness(self,w,marker,child):
        # Called on a fresh checker: newly introduced lexical sites persist.
        assigned=[]
        for p,val in w['phrase']['analyses'].items():assigned.append((int(p),reading(val)))
        for p,k in [(w['antecedent'],'noun'),(marker,'pronoun'),(child,'child_verb'),(w['parent'],'parent_verb'),(w['via'],'nonfinite_verb')]:
            if p is not None:assigned.append((p,reading(w[k])))
        if w['subject'] is not None:assigned.append((w['subject'],reading(w['subject_reading'])))
        constraints=[]
        for p,r in assigned:
            self.site(p);assert r in self.adapter.analyze(self.tokens[p])
            constraints.append(self.rb[p][self.adapter.analyze(self.tokens[p]).index(r)])
        head=w['antecedent'];via=w['via']
        for key in ('Gender','Number'):constraints.append(self.f[head,key]==self.f[marker,key])
        for p,value in w['phrase']['analyses'].items():
            p=int(p)
            if value['pos'] in ('ADJ','NUM','PRON','VPAR'):
                for key in DOMAINS:constraints.append(self.f[head,key]==self.f[p,key])
        for key,value in w['phrase'].get('agreement',{}).items():constraints.append(self.f[head,key]==value)
        if w['subject'] is not None:
            for key in ('Gender','Number'):constraints.append(self.f[via,key]==self.f[w['subject'],key])
        constraints.append(z3.Not(self.null[via]))
        return z3.And(constraints)


def run():
    counts=Counter()
    for filename in ('manifest.json','evaluation-manifest.json'):
        for path,sha in load(OUT/filename)['inputs'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
    adapter=FrozenAdapter(load(OUT/'morphology-lattice.json'));dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json')
    predictions=[next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted')) for i in range(len(dev))]
    contexts={};models={};saved={}
    def validate_serialized(t,p,scopes,bounds,options,record):
        expected={i for i,word in enumerate(t) if i not in p and any(
            r.pos=='V' and r.get('Mood')=='INF' and r.get('Voice')=='ACTIVE' or
            r.pos=='VPAR' and r.get('Case')=='NOM' and r.get('Voice')=='ACTIVE'
            for r in adapter.analyze(word))}
        assert expected=={r['position'] for r in record['records']}
        partition={}
        for index,component in enumerate(record['components']):
            for nf in component['positions']:
                assert nf not in partition;partition[nf]=index
        assert set(partition)==expected
        for a,b in combinations(sorted(expected),2):
            if partition[a]==partition[b]:continue
            for x in record['candidates'][str(a)]:
                for y in record['candidates'][str(b)]:
                    assert not (set(x['readings']) & set(y['readings']))
                    assert not (options['noncrossing'] and crossing(a,x['parent'],b,y['parent']))
        for comp in record['components']:
            checker=Independent(t,p,adapter,scopes,bounds,options,record,comp['positions'])
            sat=checker.query();assert sat==comp['satisfiable'];counts['independent_components']+=1
            for nf in comp['positions']:
                rec=next(r for r in record['records'] if r['position']==nf)
                pool=record['candidates'][str(nf)];parents=sorted({c['parent'] for c in pool})
                possible=[owner for owner in parents if checker.query(checker.owner(nf,owner))]
                unresolved=checker.query(checker.null[nf])
                assert possible==rec['possible_parents'] and unresolved==rec['unresolved_possible']
                assert bool(alternatives(adapter,t[nf]))==rec['selection_optional']
                counts['independent_owner_projections']+=1
    for c in load(OUT/'controlled.json'):
        scopes=tuple(map(tuple,c['scopes']))
        for arm,opts in ARMS.items():
            actual=Ownership(c['tokens'],c['predicates'],adapter,scopes=scopes,boundaries=(len(c['tokens']),),**opts).serializable()
            assert normalized(actual)==c['outputs'][arm];counts['controlled_replays']+=1
            validate_serialized(c['tokens'],c['predicates'],scopes,(len(c['tokens']),),opts,c['outputs'][arm])
    for row in load(OUT/'ownership.json'):
        i=row['stream'];s=dev[i];p=predictions[i];mode=row['mode'];bounds=row['boundaries'];arm=row['arm']
        scopes=({int(m):v['target'] for m,v in s['markers'].items() if v['kind']=='relative'} if mode=='reference_scope' else
            {m['position']:m['target'] for m in p['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None})
        scope_tuple=tuple(scopes.items());boundaries=s['boundaries'] if bounds=='reference' else ()
        model=Ownership(s['tokens'],s['finite'],adapter,scopes=scope_tuple,boundaries=boundaries,**ARMS[arm])
        key=(i,mode,bounds,arm);models[key]=model;saved[key]=row['ownership'];contexts[key]=(scope_tuple,boundaries)
        assert normalized(model.serializable())==row['ownership'];counts['ownership_replays']+=1
        validate_serialized(s['tokens'],s['finite'],scope_tuple,boundaries,ARMS[arm],row['ownership'])
    base={ (r['stream'],r['mode'],r['boundaries'],r['marker']):r for r in load(FIFTEEN/'predictions.json') if r['arm']=='constituent_nonfinite_declared_frames'}
    rows=load(OUT/'predictions.json')
    for r in rows:
        key=(r['stream'],r['mode'],r['boundaries']);prior=base[*key,r['marker']]
        if r['arm']=='original':assert r['result']==prior['result'];continue
        arm='independent' if r['arm']=='nearest' else r['arm'];context=(*key,arm);model=models[context]
        actual=filter_bridges(prior['result'],model,r['marker'],r['child'],nearest=r['arm']=='nearest')
        assert normalized(actual)==r['result'];counts['relative_replays']+=1
        s=dev[r['stream']]
        for w in r['result']['chains']:
            check_witness(s['tokens'],s['finite'],r['marker'],r['child'],w,adapter,True);counts['local_relative_SMT_witnesses']+=1
        if r['arm']=='nearest':continue
        for w in (*r['result']['chains'],*r['result'].get('rejected',[])):
            if w['via'] is None:assert w['ownership']=='direct';continue
            nf=w['via'];record=saved[context]
            component=next((c for c in record['components'] if nf in c['positions']),None)
            if component is None or not record['candidates'][str(nf)]:status='unlicensed'
            elif not component['satisfiable']:status='conflict'
            else:
                scopes,bounds=contexts[context]
                checker=Independent(s['tokens'],s['finite'],adapter,scopes,bounds,ARMS[arm],record,component['positions'])
                binding=checker.bind_witness(w,r['marker'],r['child']);owner=checker.owner(nf,w['parent'])
                status='excluded' if not checker.query(binding,owner) else 'ambiguous' if checker.query(binding,z3.Not(owner)) else 'entailed'
            assert status==w['ownership'],(r,w,status);counts['independent_bridge_ownership_checks']+=1
    truth=ownership_truth(dev);assert normalized(truth)==load(OUT/'evaluation-truth.json');report=load(OUT/'report.json')
    rtruth=reference_paths(dev);ownership_rows=load(OUT/'ownership.json')
    for k,v in report['ownership'].items():
        mode,bounds,arm=k.split('/')
        assert ownership_metrics([r for r in ownership_rows if (r['mode'],r['boundaries'],r['arm'])==(mode,bounds,'independent' if arm=='nearest' else arm)],truth,nearest=arm=='nearest')==v
        counts['metric_replays']+=1
    for k,v in report['relative'].items():
        mode,bounds,arm=k.split('/')
        assert relative_metrics([r for r in rows if (r['mode'],r['boundaries'],r['arm'])==(mode,bounds,arm)],rtruth)==v
        counts['metric_replays']+=1
    def ids(obj):
        if isinstance(obj,dict):
            for k,v in obj.items():
                if k=='sent_id':yield str(v)
                else:yield from ids(v)
        elif isinstance(obj,list):
            for v in obj:yield from ids(v)
    reserved=set(ids(load(RESERVE)));used={s['sent_id'] for stream in dev for s in stream['sentences']}
    assert len(reserved)==200 and not reserved & used
    save(OUT/'validation.json',{'passed':True,**counts,'reserved_ids_disjoint':len(reserved),
        'scope':'Independent Boolean CSP projections and conditional ownership checks, lexical/structural licenses, local witness SMT, artifact and metric replay; not linguistic adjudication.'})
    print(load(OUT/'validation.json'))

if __name__=='__main__':run()
