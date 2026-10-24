"""Artifact replay plus an independent SMT check of each local witness."""
import hashlib
import json
from pathlib import Path
from collections import Counter
import z3
from voynich_smt.grammar_diagnostic import MorphAnalysis,LatinAdapter
from voynich_smt.relative_constituents import infer
from benchmarks.grammar_relative_constituents_iteration15 import OUT,NINE,TEN,RESERVE,ARMS,load,save,signature
from benchmarks.grammar_relative_constituents_iteration15_evaluate import reference_paths,metrics

class FrozenAdapter(LatinAdapter):
    def __init__(self,lattice):self.lattice=lattice
    def analyze(self,word):
        return tuple(MorphAnalysis(r['pos'],tuple(map(tuple,r['features']))) for r in self.lattice[word])


def normalized(value):return json.loads(json.dumps(value))


def check_witness(tokens,predicates,marker,child,w,adapter,frames):
    """Encode simultaneous reading, case, gender, number and role constraints.

    This does not call inference's argument or constituency functions. It checks
    local feasibility, not the completeness of the candidate pool or a full parse.
    """
    selected={}
    def add(position,value):
        r=MorphAnalysis(value['pos'],tuple(map(tuple,value['features'])))
        assert r in adapter.analyze(tokens[position]),(position,value)
        if position in selected:assert selected[position]==r,(position,selected[position],r)
        selected[position]=r
    head=w['antecedent'];parent=w['parent'];via=w['via'];phrase=w['phrase']
    for p,value in phrase['analyses'].items():add(int(p),value)
    for p,key in [(head,'noun'),(marker,'pronoun'),(child,'child_verb'),(parent,'parent_verb')]:add(p,w[key])
    if via is not None:add(via,w['nonfinite_verb'])
    if w['subject'] is not None:add(w['subject'],w['subject_reading'])
    for p in selected:
        if p in predicates:assert selected[p].pos=='V' and selected[p].get('Mood') in ('IND','SUB','IMP')
    solver=z3.Solver();domains={'Gender':['M','F','N'],'Number':['S','P'],'Case':['NOM','ACC','GEN','DAT','ABL','VOC','LOC']};variables={}
    for p,r in selected.items():
        for key,values in domains.items():
            var=z3.Int(f'{key}_{p}');variables[p,key]=var
            choices=({'M','F'} if key=='Gender' and r.get(key)=='C' else set(values) if r.get(key) in (None,'X','0') else {r.get(key)})
            solver.add(z3.Or([var==values.index(v) for v in sorted(choices) if v in values]))
    eq=lambda a,b,k:variables[a,k]==variables[b,k]
    isvalue=lambda p,k,v:variables[p,k]==domains[k].index(v)
    solver.add(eq(head,marker,'Gender'),eq(head,marker,'Number'))
    for pos in phrase['analyses']:
        p=int(pos)
        if selected[p].pos in ('ADJ','NUM','PRON','VPAR'):
            solver.add(*[eq(head,p,k) for k in domains])
    for key,value in phrase.get('agreement',{}).items():solver.add(isvalue(head,key,value))
    def role_constraints(label,nom,verb,prep):
        reading=selected[verb]
        if label=='subject':
            expected='1' if tokens[nom] in ('ego','nos') else '2' if tokens[nom] in ('tu','uos','vos') else '3'
            return z3.And(isvalue(nom,'Case','NOM'),eq(nom,verb,'Number'),
                z3.BoolVal(reading.pos=='V' and reading.get('Mood') in ('IND','SUB','IMP') and reading.get('Person')==expected))
        if label=='object':
            licensed=reading.get('VerbKind')=='TRANS' or (frames and reading.get('VerbRoot') in ('hab','loc'))
            return z3.And(isvalue(nom,'Case','ACC'),z3.BoolVal(licensed and reading.get('Voice')=='ACTIVE'))
        if label=='prepositional_oblique':
            assert prep is not None and any(r.pos=='PREP' for r in adapter.analyze(tokens[prep]))
            return z3.Or([isvalue(nom,'Case',case) for case in adapter.GOVERNMENT[tokens[prep]]])
        assert label=='passive_instrument'
        return z3.And(isvalue(nom,'Case','ABL'),z3.BoolVal(reading.get('Voice')=='PASSIVE' and reading.get('VerbKind')!='DEP'))
    relative_prep=marker-1 if marker and tokens[marker-1] in adapter.GOVERNMENT else None
    solver.add(role_constraints(w['relative_role'],marker,child,relative_prep))
    solver.add(role_constraints(w['governing_role'],head,via if via is not None else parent,phrase['argument_preposition']))
    if via is not None:
        r=selected[via]
        assert r.get('Voice')=='ACTIVE'
        if r.pos=='VPAR':
            assert w['subject'] is not None and selected[parent].get('Person')=='3'
            solver.add(isvalue(via,'Case','NOM'),eq(via,parent,'Number'),
                eq(via,w['subject'],'Number'),eq(via,w['subject'],'Gender'),
                role_constraints('subject',w['subject'],parent,None))
        else:
            assert r.pos=='V' and r.get('Mood')=='INF' and selected[parent].get('VerbRoot') in ('deb','poss')
    assert solver.check()==z3.sat,w


def run():
    for filename in ('manifest.json','evaluation-manifest.json'):
        for path,sha in load(OUT/filename)['inputs'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
    adapter=FrozenAdapter(load(OUT/'morphology-lattice.json'));checked=Counter()
    for c in load(OUT/'controlled.json'):
        for arm,options in ARMS.items():
            output=infer(c['tokens'],c['predicates'],c['marker'],c['child'],adapter,**options)
            assert normalized(output)==c['outputs'][arm];checked['controlled_replays']+=1
            for witness in output['chains']:
                check_witness(c['tokens'],c['predicates'],c['marker'],c['child'],witness,adapter,options['object_frames']);checked['controlled_SMT_witnesses']+=1
        assert normalized(signature(c['outputs']['constituent_nonfinite_declared_frames']))==c['expected_chains']
    dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json');rows=load(OUT/'predictions.json')
    predictions=[next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted')) for i in range(len(dev))]
    for r in rows:
        s=dev[r['stream']];pred=predictions[r['stream']];options=ARMS[r['arm']]
        scopes=({int(m):v['target'] for m,v in s['markers'].items() if v['kind']=='relative'} if r['mode']=='reference_scope' else
            {m['position']:m['target'] for m in pred['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None})
        result=({'status':'missing_scope','parents':[],'antecedents':[],'chains':[]} if r['child'] is None else
            infer(s['tokens'],s['finite'],r['marker'],r['child'],adapter,scopes=tuple(scopes.items()),
                boundaries=s['boundaries'] if r['boundaries']=='reference' else (),**options))
        assert normalized(result)==r['result'];checked['natural_replays']+=1
        for witness in result['chains']:
            check_witness(s['tokens'],s['finite'],r['marker'],r['child'],witness,adapter,options['object_frames']);checked['natural_SMT_witnesses']+=1
    truth=reference_paths(dev);assert normalized(list(truth.values()))==load(OUT/'evaluation-truth.json')
    report=load(OUT/'report.json')
    for key,value in report['summary'].items():
        mode,bounds,arm=key.split('/')
        assert metrics([r for r in rows if (r['mode'],r['boundaries'],r['arm'])==(mode,bounds,arm)],truth)==value
        checked['metric_conditions']+=1
    def ids(obj):
        if isinstance(obj,dict):
            for k,v in obj.items():
                if k=='sent_id':yield str(v)
                else:yield from ids(v)
        elif isinstance(obj,list):
            for v in obj:yield from ids(v)
    reserved=set(ids(load(RESERVE)));used={s['sent_id'] for stream in dev for s in stream['sentences']}
    assert len(reserved)==200 and not reserved & used
    checked['reserved_ids_disjoint']=len(reserved)
    save(OUT/'validation.json',{'passed':True,**checked,
        'scope':'Exact replay, independently encoded local SMT witnesses, annotation/metric replay; not linguistic adjudication or complete-parsing proof.'})
    print(load(OUT/'validation.json'))

if __name__=='__main__':run()
