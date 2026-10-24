"""Independent exhaustive unit-cover checks, without invoking the primary CSP.

For an open-owner model, unrequired NFs can stay unknown. Every satisfying
assignment has a subset of selected units covering all required NFs, so exhaustive
unit-cover enumeration is complete for these feasibility/owner queries.
"""
from collections import Counter
from itertools import combinations
import hashlib
from pathlib import Path
from voynich_smt.grammar_diagnostic import MorphAnalysis
from voynich_smt.complement_units import ComplementModel
from benchmarks.grammar_relative_constituents_iteration15_validate import FrozenAdapter,normalized
from benchmarks.grammar_complement_units_iteration17 import OUT,SIXTEEN,NINE,TEN,RESERVE,ARMS,load,save
from benchmarks.grammar_complement_units_iteration17_evaluate import coverage

DOMAIN={'Gender':{'M','F','N'},'Number':{'S','P'},'Case':{'NOM','ACC','GEN','DAT','ABL','VOC','LOC'}}
def r(value):return MorphAnalysis(value['pos'],tuple(map(tuple,value['features'])))
def crossing(a,b,c,d):
    a,b=sorted((a,b));c,d=sorted((c,d))
    return a<c<b<d or c<a<d<b


class Exhaustive:
    def __init__(self,tokens,predicates,adapter,scopes,bounds,options,saved):
        self.tokens=tokens;self.predicates=predicates;self.adapter=adapter;self.scopes=scopes;self.bounds=bounds;self.options=options
        self.units=saved['units'];self.states=0;self.proposed={rec['position'] for rec in saved['records']}
        for values in saved['candidates'].values():
            for c in values:
                self.check_candidate(c)
                assert any(u['members']==[c['nonfinite']] and u['parts']==[c] for u in self.units)
        for u in self.units:
            members=u['members'];assert len(members) in (1,2) and len(set(members))==len(members)
            assert members==[c['nonfinite'] for c in u['parts']]
            merged={}
            for c in u['parts']:
                assert c['parent']==u['parent'];self.check_candidate(c)
                for pos,val in c['readings'].items():
                    if pos in merged:assert merged[pos]==val
                    merged[pos]=val
            if len(members)==2:
                assert options['coordination'] and u['kind']=='coordinated_infinitives'
                assert all(c['kind']!='shared_subject_participle' for c in u['parts'])
                cue=u['cue'];assert cue and cue['members']==members
                self.check_cue(cue,saved)
                for pos,val in cue['readings'].items():
                    if pos in merged:assert merged[pos]==val
                    merged[pos]=val
            else:assert u['cue'] is None and u['kind']==u['parts'][0]['kind']
            assert merged==u['readings']
            for pos,val in merged.items():assert r(val) in adapter.analyze(tokens[int(pos)])
        self.by_nf={nf:[i for i,u in enumerate(self.units) if nf in u['members']] for nf in (rec['position'] for rec in saved['records'])}

    def geometry(self,a,b):
        low,high=sorted((a,b));assert high-low<=32
        assert sum(a>=x for x in self.bounds)==sum(b>=x for x in self.bounds)
        assert not any(low<f<high and not any(low<m<=f<=c<high for m,c in self.scopes if m<c) for f in self.predicates)
        assert not any(a<m<=b<=c or b<m<=a<=c for m,c in self.scopes if m<c)

    def check_candidate(self,c):
        nf,parent=c['nonfinite'],c['parent'];reads={int(p):r(v) for p,v in c['readings'].items()}
        assert nf not in self.predicates and parent in self.predicates
        self.geometry(nf,parent)
        for p,read in reads.items():assert read in self.adapter.analyze(self.tokens[p])
        nr,pr=reads[nf],reads[parent]
        assert pr.pos=='V' and pr.get('Mood') in ('IND','SUB','IMP')
        kind=c['kind']
        if kind=='shared_subject_participle':
            sr=reads[c['subject']];assert nr.pos=='VPAR' and nr.get('Voice')=='ACTIVE' and nr.get('Case')=='NOM'
            assert sr.pos in ('N','PRON') and sr.get('Case')=='NOM'
            assert nr.get('Number')==sr.get('Number')==pr.get('Number') and pr.get('Person')=='3'
            assert self.adapter.agrees(nr,sr,('Gender','Number'))
            assert abs(c['subject']-nf)<=8 and c['subject'] not in self.predicates and c['subject'] not in self.proposed
            assert sum(c['subject']>=b for b in self.bounds)==sum(parent>=b for b in self.bounds)
            assert self.tokens[c['subject']] not in ('ego','nos','tu','uos','vos')
            assert not any(min(c['subject'],parent)<f<max(c['subject'],parent) and not any(min(c['subject'],parent)<m<=f<=end<max(c['subject'],parent) for m,end in self.scopes if m<end) for f in self.predicates)
        else:
            assert c['subject'] is None and nr.pos=='V' and nr.get('Mood')=='INF' and nr.get('Voice')=='ACTIVE'
            if kind=='modal':assert pr.get('VerbRoot') in ('deb','poss') and pr.get('Voice')=='ACTIVE'
            elif kind=='passive_reporting':assert pr.get('VerbRoot') in ('cred','dic','fer') and pr.get('Voice')=='PASSIVE'
            else:
                assert self.options['expanded'] and pr.get('Voice')=='ACTIVE'
                if kind=='negative_imperative':assert pr.get('VerbRoot')=='nol' and pr.get('Mood')=='IMP' and pr.get('Person')=='2'
                elif kind=='habitual':assert pr.get('VerbRoot')=='sol'
                else:
                    assert kind=='perception_aci' and pr.get('VerbRoot')=='uid'
                    sub=c['embedded_subject'];sr=reads[sub]
                    assert min(nf,parent)<sub<max(nf,parent) and abs(sub-nf)<=3 and sub not in self.predicates and sub not in self.proposed
                    assert sr.pos in ('N','PRON') and sr.get('Case')=='ACC'

    def check_cue(self,cue,saved):
        a,b=cue['members'];positions=cue['marker_positions'];assert a<b and b-a<=8
        assert not any(a<f<b for f in self.predicates) and not any(a<end<=b for end in self.bounds)
        infs=sorted(rec['position'] for rec in saved['records'] if any(read.pos=='V' and read.get('Mood')=='INF' and read.get('Voice')=='ACTIVE' for read in self.adapter.analyze(self.tokens[rec['position']])))
        assert infs[infs.index(a)+1]==b
        if cue['kind']=='paired_ne_c':
            assert self.tokens[a-2:a]==['ne','c'] and self.tokens[b-2:b]==['ne','c']
            assert positions==[b-2,b-1] and not cue['readings']
        else:
            assert cue['kind']=='conjunction' and len(positions)==1
            p=positions[0];assert a<p<b and self.tokens[p] in ('et','aut','uel','nec','neque')
            assert r(cue['readings'][str(p)]).pos=='CONJ'
        for p in range(a+1,b):
            if p not in positions:assert any(read.pos in ('N','PRON','ADJ','NUM','PREP','ADV','VPAR') for read in self.adapter.analyze(self.tokens[p]))

    def coherent(self,selected):
        merged={};occupied=set();slots=set();arcs=[];equalities=[]
        for index in selected:
            unit=self.units[index];members=set(unit['members']);parent=unit['parent']
            if members & occupied:return False
            occupied.update(members)
            if unit['kind']!='shared_subject_participle':
                if parent in slots:return False
                slots.add(parent)
            for member in members:
                if any(crossing(member,parent,a,b) for a,b in arcs):return False
                arcs.append((member,parent))
            for pos,value in unit['readings'].items():
                pos=int(pos);read=r(value)
                if pos in merged and merged[pos]!=read:return False
                merged[pos]=read
            for c in unit['parts']:
                if c['subject'] is not None:
                    equalities.extend(((c['nonfinite'],key),(c['subject'],key)) for key in ('Gender','Number'))
        # Simultaneously bind wildcard/common gender and number, rather than
        # independently accepting pairwise compatibility with an unknown value.
        roots={};domains={}
        def find(x):
            roots.setdefault(x,x)
            if roots[x]!=x:roots[x]=find(roots[x])
            return roots[x]
        for a,b in equalities:
            ra,rb=find(a),find(b)
            if ra!=rb:roots[ra]=rb
        for pos,read in merged.items():
            for key,domain in DOMAIN.items():
                value=read.get(key);allowed={'M','F'} if key=='Gender' and value=='C' else domain if value in (None,'X','0') else {value}
                root=find((pos,key));domains[root]=domains.get(root,set(domain)) & allowed
        return all(domains.values())

    def witness(self,requirements):
        required={}
        for nf,parent in requirements:
            if nf in required and required[nf]!=parent:return None
            required[nf]=parent
        def search(selected,covered):
            self.states+=1
            if not set(required)-covered:return selected
            nf=min(set(required)-covered)
            for index in self.by_nf.get(nf,[]):
                unit=self.units[index]
                if any(member in required and required[member]!=unit['parent'] for member in unit['members']):continue
                if self.coherent((*selected,index)):
                    result=search((*selected,index),covered|set(unit['members']))
                    if result is not None:return result
            return None
        return search((),set())


def run():
    counts=Counter()
    for filename in ('manifest.json','evaluation-manifest.json'):
        for p,sha in load(OUT/filename)['inputs'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha,p
    adapter=FrozenAdapter(load(OUT/'morphology-lattice.json'));dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json')
    for c in load(OUT/'controlled.json'):
        for arm,opts in ARMS.items():
            model=ComplementModel(c['tokens'],c['predicates'],adapter,boundaries=(len(c['tokens']),),**opts)
            actual=model.serializable();assert normalized(actual)==c['outputs'][arm]['model']
            checker=Exhaustive(c['tokens'],c['predicates'],adapter,(),(len(c['tokens']),),opts,actual)
            feasible=checker.witness(c['requirements']) is not None
            assert feasible==c['outputs'][arm]['requirements_feasible'];counts['controlled_models']+=1
    saved=load(OUT/'models.json');queries=load(OUT/'reference-queries.json');report=load(OUT/'report.json');truth=load(SIXTEEN/'evaluation-truth.json')
    for row in saved:
        s=dev[row['stream']];pred=next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(row['stream'],'oof','interactions','predicted','unrestricted'))
        scopes=tuple((int(m),v['target']) for m,v in s['markers'].items() if v['kind']=='relative') if row['mode']=='reference_scope' else tuple((m['position'],m['target']) for m in pred['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None)
        bounds=s['boundaries'] if row['boundaries']=='reference' else ();opts=ARMS[row['arm']]
        model=ComplementModel(s['tokens'],s['finite'],adapter,scopes=scopes,boundaries=bounds,**opts)
        actual=model.serializable();assert normalized(actual)==row['model'];counts['natural_models']+=1
        checker=Exhaustive(s['tokens'],s['finite'],adapter,scopes,bounds,opts,row['model'])
        for rec in row['model']['records']:
            possible=[p for p in rec['candidate_parents'] if checker.witness([(rec['position'],p)]) is not None]
            assert possible==rec['possible_parents'] and rec['unknown_possible'] and rec['firm_owner'] is None
            counts['independent_owner_projections']+=1
        q=next(q for q in queries if (q['stream'],q['mode'],q['boundaries'],q['arm'])==(row['stream'],row['mode'],row['boundaries'],row['arm']))
        local={t['position']:t for t in truth if t['stream']==row['stream']}
        context={rr['arm']:rr for rr in saved if (rr['stream'],rr['mode'],rr['boundaries'])==(row['stream'],row['mode'],row['boundaries'])}
        for label,source_arm in [('common','base_open'),('expanded','units_open')]:
            expected=[(rec['position'],local[rec['position']]['owner']) for rec in context[source_arm]['model']['records']
                if rec['position'] in local and local[rec['position']]['owner'] in rec['possible_parents']]
            assert normalized(expected)==q[f'{label}_requirements']
            witness=checker.witness(q[f'{label}_requirements']);assert (witness is not None)==q[f'{label}_feasible']
            assert model.can_assign(q[f'{label}_requirements'])==q[f'{label}_feasible'];counts['reference_subgraph_checks']+=1
        counts['enumerated_search_states']+=checker.states
    for key,value in report['coverage'].items():
        mode,bounds,arm=key.split('/')
        assert coverage([row for row in saved if (row['mode'],row['boundaries'],row['arm'])==(mode,bounds,arm)],truth)==value
        counts['coverage_conditions']+=1
    for key,value in report['feasibility'].items():
        mode,bounds,arm=key.split('/')
        selected=[q for q in queries if (q['mode'],q['boundaries'],q['arm'])==(mode,bounds,arm)]
        expected={'common_streams':sum(bool(q['common_requirements']) for q in selected),
            'common_feasible':sum(bool(q['common_requirements']) and q['common_feasible'] for q in selected),
            'expanded_streams':sum(bool(q['expanded_requirements']) for q in selected),
            'expanded_feasible':sum(bool(q['expanded_requirements']) and q['expanded_feasible'] for q in selected)}
        assert expected==value;counts['feasibility_conditions']+=1
    lookup={(t['stream'],t['position']):t for t in truth}
    audits=load(OUT/'coordination-audit.json')
    expected_pairs={(row['stream'],tuple(u['members'])) for row in saved
        if (row['mode'],row['boundaries'],row['arm'])==('reference_scope','hidden','units_open')
        for u in row['model']['units'] if len(u['members'])==2}
    assert expected_pairs=={(c['stream'],tuple(c['members'])) for c in audits}
    for c in audits:
        a,b=c['members'];left=lookup.get((c['stream'],a));right=lookup.get((c['stream'],b));s=dev[c['stream']]
        offset=next(begin for begin,end in zip((0,*s['boundaries'][:-1]),s['boundaries']) if begin<=b<end)
        flag=bool(left and right and left['form']=='Inf' and right['form']=='Inf' and left['owner'] is not None and
            left['owner']==right['owner'] and right['path'][0]['relation'].split(':')[0]=='conj' and
            right['path'][0]['head'] is not None and right['path'][0]['head']+offset==a)
        assert flag==c['annotated_direct_coordination'];counts['coordination_audits']+=1
    assert len(audits)==report['coordination_pairs']
    assert sum(c['annotated_direct_coordination'] for c in audits)==report['annotated_direct_coordination_pairs']
    def ids(obj):
        if isinstance(obj,dict):
            for key,value in obj.items():
                if key=='sent_id':yield str(value)
                else:yield from ids(value)
        elif isinstance(obj,list):
            for item in obj:yield from ids(item)
    reserved=set(ids(load(RESERVE)));used={s['sent_id'] for stream in dev for s in stream['sentences']}
    assert len(reserved)==200 and not reserved & used
    save(OUT/'validation.json',{'passed':True,**counts,'reserved_ids_disjoint':len(reserved),
        'scope':'Artifact replay, independently checked licenses, exhaustive compatible unit covers and wildcard unification; not full-parse or linguistic correctness proof.'})
    print(load(OUT/'validation.json'))

if __name__=='__main__':run()
