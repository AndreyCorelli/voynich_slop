"""Joint nonfinite ownership; frozen iteration15 relative-candidate pools."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import time
from voynich_smt.nonfinite_ownership import Ownership,filter_bridges
from voynich_smt.relative_constituents import ConstituentAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from benchmarks.grammar_relative_constituents_iteration15 import NINE,TEN,RESERVE,load,save,OUT as FIFTEEN

OUT=FIFTEEN.parent/'iteration16-v2'
ARMS={
    'independent':dict(capacity=False,noncrossing=False,reporting=True),
    'capacity':dict(capacity=True,noncrossing=False,reporting=True),
    'joint':dict(capacity=True,noncrossing=True,reporting=True),
    'no_reporting':dict(capacity=True,noncrossing=True,reporting=False),
}
# Values: nonfinite word -> (all feasible owner surfaces, status).
PROBES=[
 ('crossing_competition','creditur agricola fecundare qui cantat puellam diligere debet',('creditur','cantat','debet'),(('qui','cantat'),),
    {'fecundare':(['creditur'],'unique'),'diligere':(['debet'],'unique')}),
 ('farther_owner_same_sentence','creditur agricola semper diligenter multum laborare et puellam diligere debet dum pueri currunt',('creditur','debet','currunt'),(),
    {'laborare':(['creditur'],'unique'),'diligere':(['debet'],'unique')}),
 ('capacity_forces_farther','pueri currunt creditur agricola laborare debet puellam diligere',('currunt','creditur','debet'),(),
    {'laborare':(['creditur'],'unique'),'diligere':(['debet'],'unique')}),
 ('genuine_ambiguity','pueri currunt creditur agricola laborare debet',('currunt','creditur','debet'),(),
    {'laborare':(['creditur','debet'],'ambiguous')}),
 ('active_reporting_outside_inventory','pueri currunt credit agricola laborare debet',('currunt','credit','debet'),(),
    {'laborare':(['debet'],'unique')}),
 ('shared_subject_participle','pueri currunt agricola accedit habens puellam bonam quae cantat',('currunt','accedit','cantat'),(('quae','cantat'),),
    {'habens':(['accedit'],'optional')}),
 ('participle_number_mismatch','pueri currunt agricola accedit habentes puellam bonam quae cantat',('currunt','accedit','cantat'),(('quae','cantat'),),
    {'habentes':([],'unlicensed')}),
 ('unsupported_coordination','pueri currunt puella ridet agricola debet laborare et ambulare',('currunt','ridet','debet'),(),
    {'laborare':([],'conflict'),'ambulare':([],'conflict')}),
 ('unlicensed_infinitive','pueri currunt agricola ridet laborare puella cantat',('currunt','ridet','cantat'),(),
    {'laborare':([],'unlicensed')}),
 ('conflict_is_local','pueri currunt agricola debet laborare et ambulare puella ridet creditur puer fecundare',('currunt','debet','ridet','creditur'),(),
    {'laborare':([],'conflict'),'ambulare':([],'conflict'),'fecundare':(['creditur'],'unique')}),
]


def arguments(probe):
    name,text,pwords,scope_words,expected_words=probe;tokens=text.split()
    predicates=[tokens.index(w) for w in pwords];scopes=tuple((tokens.index(m),tokens.index(c)) for m,c in scope_words)
    expected={tokens.index(nf):dict(possible_parents=sorted(tokens.index(p) for p in parents),status=status) for nf,(parents,status) in expected_words.items()}
    return tokens,predicates,scopes,expected


def run():
    if OUT.exists():raise ValueError('Preserve saved artifacts')
    start=time.monotonic();adapter=ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))
    controlled=[]
    for probe in PROBES:
        tokens,predicates,scopes,expected=arguments(probe)
        outputs={arm:Ownership(tokens,predicates,adapter,scopes=scopes,boundaries=(len(tokens),),**opts).serializable() for arm,opts in ARMS.items()}
        observed={r['position']:{k:r[k] for k in ('possible_parents','status')} for r in outputs['joint']['records']}
        assert observed==expected,(probe[0],observed,expected)
        controlled.append(dict(name=probe[0],tokens=tokens,predicates=predicates,scopes=scopes,expected=expected,outputs=outputs))
    # Probes and constraints are fixed before source development is evaluated.
    dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json')
    previous=load(FIFTEEN/'predictions.json')
    previous={(r['stream'],r['mode'],r['boundaries'],r['marker']):r for r in previous if r['arm']=='constituent_nonfinite_declared_frames'}
    rows=[];ownership=[];queries=0
    for i,s in enumerate(dev):
        pred=next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted'))
        gold={int(m):v['target'] for m,v in s['markers'].items() if v['kind']=='relative'}
        predicted={m['position']:m['target'] for m in pred['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None}
        for mode,scopes in [('reference_scope',gold),('predicted_scope',predicted)]:
            for bounded in (False,True):
                bounds='reference' if bounded else 'hidden'
                models={arm:Ownership(s['tokens'],s['finite'],adapter,scopes=tuple(scopes.items()),boundaries=s['boundaries'] if bounded else (),**opts) for arm,opts in ARMS.items()}
                for arm,model in models.items():
                    ownership.append(dict(stream=i,mode=mode,boundaries=bounds,arm=arm,ownership=model.serializable()))
                for marker in sorted(set(gold)|set(scopes)):
                    base=previous[i,mode,bounds,marker]
                    rows.append({**base,'arm':'original'})
                    for arm in ('independent','capacity','joint','no_reporting','nearest'):
                        model=models['independent' if arm=='nearest' else arm]
                        result=filter_bridges(base['result'],model,marker,base['child'],nearest=arm=='nearest')
                        rows.append({**base,'arm':arm,'result':result})
                queries+=sum(m.queries for m in models.values())
        if i and i%20==0:print(f'{i}/{len(dev)} streams',flush=True)
    OUT.mkdir(parents=True)
    save(OUT/'controlled.json',controlled);save(OUT/'ownership.json',ownership);save(OUT/'predictions.json',rows)
    words=sorted({w for s in dev for w in s['tokens']}|{w for c in controlled for w in c['tokens']})
    save(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in words})
    inputs=[NINE/'development-truth.json',TEN/'predictions.json',FIFTEEN/'predictions.json',RESERVE,
        Path(__file__),Path('src/voynich_smt/nonfinite_ownership.py'),Path('src/voynich_smt/relative_constituents.py')]
    save(OUT/'manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'lexicon_resource':adapter.analyzer.resource,'arms':ARMS,'radius':32,
        'scope':'66 inspected development streams; finite positions supplied; relative candidates frozen from iteration15-v2.',
        'queries':queries,'elapsed_seconds':time.monotonic()-start})
    print(f'{len(controlled)} probes passed; {len(ownership)} ownership conditions; {len(rows)} relative conditions; {queries} SAT queries; {time.monotonic()-start:.2f}s')

if __name__=='__main__':run()
