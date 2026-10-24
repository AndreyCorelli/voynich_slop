"""Ablative participles versus nominal homographs; separate nisi ablation."""
from pathlib import Path
from dataclasses import asdict
import hashlib
from benchmarks.grammar_argument_structures_iteration20 import OUT as TWENTY,NINETEEN,SEVENTEEN,NINE,SIXTEEN,RESERVE,load,save
from benchmarks.grammar_oracle_morphology_iteration19 import OverlayAdapter
from benchmarks.grammar_relative_constituents_iteration15_validate import normalized
from voynich_smt.participial_structures import recognize
from voynich_smt.complement_units import ComplementModel
from voynich_smt.relative_constituents import ConstituentAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

OUT=TWENTY.parent/'iteration21'
ARMS={'baseline':dict(participles=False,nisi_clause=False),
      'participles':dict(participles=True,nisi_clause=False),
      'participles_nisi':dict(participles=True,nisi_clause=True)}
PROBES=[
 ('subject_before_participle','pueri currunt debet urbe capta laborare puella ridet',('currunt','debet','ridet')),
 ('participle_before_subject','pueri currunt debet capta urbe laborare puella ridet',('currunt','debet','ridet')),
 ('number_mismatch','pueri currunt debet urbibus capta laborare puella ridet',('currunt','debet','ridet')),
 ('gender_mismatch','pueri currunt debet urbe capto laborare puella ridet',('currunt','debet','ridet')),
 ('case_mismatch','pueri currunt debet urbem capta laborare puella ridet',('currunt','debet','ridet')),
 ('no_participle','pueri currunt debet urbe bona laborare puella ridet',('currunt','debet','ridet')),
 ('nisi_subject_participle','pueri currunt debet nisi uespere instante laborare puella ridet',('currunt','debet','ridet')),
 ('nisi_number_mismatch','pueri currunt debet nisi urbibus instante laborare puella ridet',('currunt','debet','ridet')),
 ('nisi_finite_barrier','pueri currunt debet nisi urbe ridet capta laborare puella cantat',('currunt','debet','ridet','cantat')),
 ('unknown_subject','pueri currunt debet zzznominal capta laborare puella ridet',('currunt','debet','ridet')),
 ('source_defensis','pueri currunt possit defensis sedibus apricare puella ridet',('currunt','possit','ridet')),
]


def analyze(tokens,predicates,adapter,model,**flags):
    units=[];parents={str(r['position']):set() for r in model['records'] if any(v.pos=='V' and v.get('Mood')=='INF' and v.get('Voice')=='ACTIVE' for v in adapter.analyze(tokens[r['position']]))}
    for i,u in enumerate(model['units']):
        if u['kind']=='shared_subject_participle':continue
        result=recognize(tokens,predicates,adapter,u,coordination=True,attachment=True,perdere_frame=True,**flags)
        units.append(dict(unit=i,result=result))
        if result['status']=='supported':
            for nf in u['members']:
                if str(nf) in parents:parents[str(nf)].add(u['parent'])
    return dict(units=units,parents={n:sorted(p) for n,p in parents.items()},firm_claims=[])


def produce(dev,models,lattice,additions):
    rows=[]
    for r in models:
        if r['arm']!='units_open':continue
        s=dev[r['stream']]
        for morphology in ('dictionary','oracle_missing'):
            a=OverlayAdapter(lattice,[v for v in additions if v['stream']==r['stream']] if morphology=='oracle_missing' else [])
            for arm,flags in ARMS.items():rows.append(dict(stream=r['stream'],mode=r['mode'],boundaries=r['boundaries'],morphology=morphology,arm=arm,result=analyze(s['tokens'],s['finite'],a,r['model'],**flags)))
    return normalized(rows)


def run():
    if OUT.exists():raise ValueError('Preserve existing artifacts')
    a=ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'));controls=[];lattice=load(TWENTY/'morphology-lattice.json')
    for name,text,pwords in PROBES:
        t=text.split();p=[t.index(w) for w in pwords];model=normalized(ComplementModel(t,p,a).serializable())
        controls.append(dict(name=name,tokens=t,predicates=p,model=model,results={arm:analyze(t,p,a,model,**flags) for arm,flags in ARMS.items()}))
        for w in t:lattice[w]=normalized([asdict(v) for v in a.analyze(w)])
    rows=produce(load(NINE/'development-truth.json'),load(SEVENTEEN/'models.json'),lattice,load(NINETEEN/'oracle-readings.json'))
    OUT.mkdir();save(OUT/'controlled.json',controls);save(OUT/'predictions.json',rows);save(OUT/'morphology-lattice.json',lattice)
    paths=[Path(__file__),Path('src/voynich_smt/participial_structures.py'),Path('src/voynich_smt/construction_spans.py'),Path('src/voynich_smt/relative_constituents.py'),
        TWENTY/'predictions.json',TWENTY/'morphology-lattice.json',NINETEEN/'oracle-readings.json',SEVENTEEN/'models.json',NINE/'development-truth.json',RESERVE]
    save(OUT/'manifest.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        grammar='Adjacent ablative nominal subject + VPAR in either order, optionally prefixed by separately enabled nisi; joint case/number/gender.',
        scope='Fixed construction interiors on inspected development; nominal and attachment alternatives retained; no owner entailment.'))
    print(f'{len(controls)} controls; {len(rows)} natural conditions')

if __name__=='__main__':run()
