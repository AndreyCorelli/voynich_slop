"""Coordination and argument-attachment diagnostic on frozen candidate units."""
from pathlib import Path
import hashlib
from dataclasses import asdict
from benchmarks.grammar_oracle_morphology_iteration19 import OUT as NINETEEN,EIGHTEEN,SEVENTEEN,NINE,SIXTEEN,RESERVE,load,save,OverlayAdapter
from benchmarks.grammar_relative_constituents_iteration15_validate import normalized
from voynich_smt.argument_structures import recognize
from voynich_smt.complement_units import ComplementModel
from voynich_smt.relative_constituents import ConstituentAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

OUT=NINETEEN.parent/'iteration20'
ARMS={'coordination':dict(coordination=True,attachment=False),
      'coordination_frame':dict(coordination=True,attachment=False,perdere_frame=True),
      'attachment':dict(coordination=False,attachment=True),
      'joint':dict(coordination=True,attachment=True,perdere_frame=True)}
PROBES=[
 ('object_coordination','pueri currunt debet puellam et librum capere puella ridet',('currunt','debet','ridet')),
 ('correlative_objects','pueri currunt potest et animam et corpus perdere puella ridet',('currunt','potest','ridet')),
 ('wrong_object_cases','pueri currunt debet puellis et libris capere puella ridet',('currunt','debet','ridet')),
 ('missing_object_coordinator','pueri currunt debet puellam librum capere puella ridet',('currunt','debet','ridet')),
 ('bad_object_modifier','pueri currunt debet puellam bonis et librum capere puella ridet',('currunt','debet','ridet')),
 ('shared_or_single_object','pueri currunt capere et accipere librum debet puella ridet',('currunt','debet','ridet')),
 ('separate_objects','pueri currunt debet puellam capere et librum accipere puella ridet',('currunt','debet','ridet')),
 ('wrong_segment_two_objects','pueri currunt debet puellam librum capere et accipere puella ridet',('currunt','debet','ridet')),
 ('ambiguous_ablative_attachment','pueri currunt creditur bona praesentia fecundare puella ridet',('currunt','creditur','ridet')),
 ('ablative_modifier_mismatch','pueri currunt creditur bonis praesentia fecundare puella ridet',('currunt','creditur','ridet')),
 ('object_not_intransitive','pueri currunt debet puellam et librum laborare puella ridet',('currunt','debet','ridet')),
]


def analyze(tokens,predicates,adapter,model,**flags):
    results=[];parents={str(r['position']):set() for r in model['records'] if any(v.pos=='V' and v.get('Mood')=='INF' and v.get('Voice')=='ACTIVE' for v in adapter.analyze(tokens[r['position']]))}
    for i,u in enumerate(model['units']):
        if u['kind']=='shared_subject_participle':continue
        result=recognize(tokens,predicates,adapter,u,**flags)
        results.append({'unit':i,'result':result})
        if result['status']=='supported':
            for nf in u['members']:
                if str(nf) in parents:parents[str(nf)].add(u['parent'])
    return {'units':results,'parents':{n:sorted(p) for n,p in parents.items()},'firm_claims':[]}


def produce(dev,models,lattice,additions):
    rows=[]
    for r in models:
        if r['arm']!='units_open':continue
        s=dev[r['stream']]
        for morphology in ('dictionary','oracle_missing'):
            adapter=OverlayAdapter(lattice,[a for a in additions if a['stream']==r['stream']] if morphology=='oracle_missing' else [])
            for arm,flags in ARMS.items():
                rows.append(dict(stream=r['stream'],mode=r['mode'],boundaries=r['boundaries'],morphology=morphology,arm=arm,
                    result=analyze(s['tokens'],s['finite'],adapter,r['model'],**flags)))
    return normalized(rows)


def run():
    if OUT.exists():raise ValueError('Preserve existing artifacts')
    adapter=ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'));controls=[]
    for name,text,pwords in PROBES:
        tokens=text.split();predicates=[tokens.index(w) for w in pwords];model=normalized(ComplementModel(tokens,predicates,adapter).serializable())
        results={arm:analyze(tokens,predicates,adapter,model,**flags) for arm,flags in ARMS.items()}
        controls.append(dict(name=name,tokens=tokens,predicates=predicates,model=model,results=results))
    lattice=load(EIGHTEEN/'morphology-lattice.json')
    for c in controls:
        for w in c['tokens']:lattice[w]=normalized([asdict(r) for r in adapter.analyze(w)])
    dev=load(NINE/'development-truth.json');models=load(SEVENTEEN/'models.json');additions=load(NINETEEN/'oracle-readings.json')
    rows=produce(dev,models,lattice,additions)
    OUT.mkdir();save(OUT/'controlled.json',controls);save(OUT/'morphology-lattice.json',lattice);save(OUT/'predictions.json',rows)
    paths=[Path(__file__),Path('src/voynich_smt/argument_structures.py'),Path('src/voynich_smt/construction_spans.py'),Path('src/voynich_smt/relative_constituents.py'),
        NINETEEN/'oracle-readings.json',EIGHTEEN/'morphology-lattice.json',SEVENTEEN/'models.json',NINE/'development-truth.json',RESERVE]
    save(OUT/'manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scope':'Inspected development only; no full clauses or owner entailments.',
        'lexical_ablation':'Explicit perd root object license only in coordination_frame and joint.',
        'grammar':'Two ACC nominal conjuncts; exterior object single/shared alternatives; bare ABL unresolved matrix/infinitive attachment.',
        'limits':{'NP':8,'coordinated_NP':12,'distinct_structures':256}})
    print(f'{len(controls)} controls; {len(rows)} natural conditions')

if __name__=='__main__':run()
