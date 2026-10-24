"""Governor coverage and coordination without forced owner completeness."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import time
from voynich_smt.complement_units import ComplementModel
from voynich_smt.relative_constituents import ConstituentAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from benchmarks.grammar_nonfinite_ownership_iteration16 import OUT as SIXTEEN,NINE,TEN,RESERVE,load,save

OUT=SIXTEEN.parent/'iteration17'
ARMS={'base_open':dict(expanded=False,coordination=False),
    'frames_open':dict(expanded=True,coordination=False),
    'units_open':dict(expanded=True,coordination=True)}
# Expected joint feasibility in base / expanded-frames / optional-pair models.
PROBES=[
 ('negative_imperative','pueri currunt nolite timere puella ridet',('currunt','nolite','ridet'),(('timere','nolite'),),(False,True,True)),
 ('habitual','pueri currunt agricola solet laborare puella ridet',('currunt','solet','ridet'),(('laborare','solet'),),(False,True,True)),
 ('perception_aci','pueri currunt instare malum uiderint puella ridet',('currunt','uiderint','ridet'),(('instare','uiderint'),),(False,True,True)),
 ('perception_no_accusative','pueri currunt instare puella uidet agricola ridet',('currunt','uidet','ridet'),(('instare','uidet'),),(False,False,False)),
 ('nonimperative_nolo_outside_inventory','pueri currunt nolit timere puella ridet',('currunt','nolit','ridet'),(('timere','nolit'),),(False,False,False)),
 ('plain_coordination','pueri currunt agricola debet laborare et ambulare puella ridet',('currunt','debet','ridet'),(('laborare','debet'),('ambulare','debet')),(False,False,True)),
 ('paired_negative','pueri currunt ne c conlocare ne c aperire debemus puella ridet',('currunt','debemus','ridet'),(('conlocare','debemus'),('aperire','debemus')),(False,False,True)),
 ('no_marker_no_unit','pueri currunt agricola debet laborare ambulare puella ridet',('currunt','debet','ridet'),(('laborare','debet'),('ambulare','debet')),(False,False,False)),
 ('finite_barrier','pueri currunt agricola debet laborare et puella potest ambulare',('currunt','debet','potest'),(('laborare','debet'),('ambulare','debet')),(False,False,False)),
 ('finite_barrier_split','pueri currunt agricola debet laborare et puella potest ambulare',('currunt','debet','potest'),(('laborare','debet'),('ambulare','potest')),(True,True,True)),
 ('optional_not_forced_join','creditur agricola laborare et puellam diligere debet dum pueri currunt',('creditur','debet','currunt'),(('laborare','creditur'),('diligere','debet')),(True,True,True)),
 ('nominal_coordination','pueri currunt agricola debet puellam et puerum diligere puella ridet',('currunt','debet','ridet'),(('diligere','debet'),),(True,True,True)),
 ('three_member_unit_unsupported','pueri currunt agricola debet laborare et ambulare et cantare puella ridet',('currunt','debet','ridet'),(('laborare','debet'),('ambulare','debet'),('cantare','debet')),(False,False,False)),
 ('passive_perception_outside_inventory','pueri currunt instare malum uidetur puella ridet',('currunt','uidetur','ridet'),(('instare','uidetur'),),(False,False,False)),
]


def arguments(probe):
    name,text,finite_words,requirements,expected=probe;tokens=text.split()
    return tokens,[tokens.index(w) for w in finite_words],[(tokens.index(n),tokens.index(p)) for n,p in requirements],expected


def run():
    if OUT.exists():raise ValueError('Preserve existing artifacts')
    start=time.monotonic();adapter=ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))
    controlled=[]
    for probe in PROBES:
        tokens,predicates,req,expected=arguments(probe);outputs={}
        for arm,opts in ARMS.items():
            model=ComplementModel(tokens,predicates,adapter,boundaries=(len(tokens),),**opts)
            outputs[arm]={'model':model.serializable(),'requirements_feasible':model.can_assign(req)}
        observed=tuple(outputs[a]['requirements_feasible'] for a in ARMS)
        assert observed==expected,(probe[0],observed,expected)
        controlled.append(dict(name=probe[0],tokens=tokens,predicates=predicates,requirements=req,expected=expected,outputs=outputs))
    # No annotation-derived requirements enter production model construction.
    dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json');records=[]
    for i,s in enumerate(dev):
        predicted=next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted'))
        gold={int(m):v['target'] for m,v in s['markers'].items() if v['kind']=='relative'}
        markers={m['position']:m['target'] for m in predicted['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None}
        for mode,scopes in [('reference_scope',gold),('predicted_scope',markers)]:
            for bounded in (False,True):
                for arm,opts in ARMS.items():
                    model=ComplementModel(s['tokens'],s['finite'],adapter,scopes=tuple(scopes.items()),boundaries=s['boundaries'] if bounded else (),**opts)
                    records.append(dict(stream=i,mode=mode,boundaries='reference' if bounded else 'hidden',arm=arm,model=model.serializable()))
    OUT.mkdir(parents=True);save(OUT/'controlled.json',controlled);save(OUT/'models.json',records)
    words=sorted({w for s in dev for w in s['tokens']}|{w for c in controlled for w in c['tokens']})
    save(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in words})
    paths=[Path(__file__),Path('src/voynich_smt/complement_units.py'),Path('src/voynich_smt/nonfinite_ownership.py'),
        Path('src/voynich_smt/relative_constituents.py'),NINE/'development-truth.json',TEN/'predictions.json',RESERVE]
    save(OUT/'manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'lexicon_resource':adapter.analyzer.resource,'arms':ARMS,'radius':32,'pair_gap':8,
        'scope':'Inspected development; supplied finite positions; every NF may have unknown owner; no fitting.',
        'elapsed_seconds':time.monotonic()-start})
    print(f'{len(controlled)} probes passed; {len(records)} natural models; {time.monotonic()-start:.2f}s')

if __name__=='__main__':run()
