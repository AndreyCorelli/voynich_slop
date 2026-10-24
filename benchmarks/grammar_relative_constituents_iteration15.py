"""Fixed construction ablations on controlled and already inspected relatives."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
from voynich_smt.relative_constituents import ConstituentAdapter,infer
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

OUT=Path('experiments/results/grammar-restoration/iteration15-v2')
NINE=OUT.parent/'iteration9'
TEN=OUT.parent/'iteration10'
FOURTEEN=OUT.parent/'iteration14-v3'
RESERVE=Path('experiments/holdouts/grammar-construction-next.json')
ARMS={
    'readings_direct':dict(constituents=False,nonfinite=False,object_frames=False),
    'constituent_direct':dict(constituents=True,nonfinite=False,object_frames=False),
    'constituent_nonfinite':dict(constituents=True,nonfinite=True,object_frames=False),
    'constituent_nonfinite_declared_frames':dict(constituents=True,nonfinite=True,object_frames=True),
}
# Expected tuples are (nominal surface, intermediate surface or None, parent).
PROBES=[
 ('subject_np','pueri currunt puella bona quae cantat hodie ridet',('currunt','cantat','ridet'),'quae','cantat',[('puella',None,'ridet')]),
 ('object_np','puer currit puellam bonam quae cantat mater diligit',('currit','cantat','diligit'),'quae','cantat',[('puellam',None,'diligit')]),
 ('participle','pueri currunt agricola accedit habens puellam bonam quae cantat',('currunt','accedit','cantat'),'quae','cantat',[('puellam','habens','accedit')]),
 ('participle_wrong_number','pueri currunt agricola accedit habentes puellam bonam quae cantat',('currunt','accedit','cantat'),'quae','cantat',[]),
 ('participle_wrong_case','pueri currunt agricola accedit habentem puellam bonam quae cantat',('currunt','accedit','cantat'),'quae','cantat',[]),
 ('infinitive_oblique','pueri currunt agricola debet in parte secreta locare quae cantat',('currunt','debet','cantat'),'quae','cantat',[('parte','locare','debet')]),
 ('relative_after_modal','pueri currunt agricola in parte secreta locare debet quae cantat',('currunt','debet','cantat'),'quae','cantat',[('parte','locare','debet')]),
 ('wrong_modal','pueri currunt agricola accedit in parte secreta locare quae cantat',('currunt','accedit','cantat'),'quae','cantat',[]),
 ('dictionary_transitive_infinitive','pueri currunt agricola debet librum bonum capere quem puer diligit',('currunt','debet','diligit'),'quem','diligit',[('librum','capere','debet')]),
 ('mixed_number','pueri currunt puellae bonae quae cantat hodie ridet',('currunt','cantat','ridet'),'quae','cantat',[]),
 ('modifier_mismatch','pueri currunt puella bonis quae cantat hodie ridet',('currunt','cantat','ridet'),'quae','cantat',[]),
 ('gender_mismatch','pueri currunt puella qui cantat hodie ridet',('currunt','cantat','ridet'),'qui','cantat',[]),
 ('ambiguous_governors','puer currit puella bona quae cantat hodie ridet',('currit','cantat','ridet'),'quae','cantat',[('puella',None,'currit'),('puella',None,'ridet')]),
 ('bare_preposition_homograph','pueri currunt aduersus qui cantat hodie ridet',('currunt','cantat','ridet'),'qui','cantat',[]),
]


def load(path):return json.loads(path.read_text())
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def signature(result):return sorted({(w['antecedent'],w['via'],w['parent']) for w in result['chains']},key=str)


def run():
    if OUT.exists():raise ValueError('Preserve saved artifacts')
    start=time.monotonic();adapter=ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))
    controlled=[]
    for name,text,pwords,mword,cword,expected_words in PROBES:
        tokens=text.split();predicates=[tokens.index(w) for w in pwords];marker=tokens.index(mword);child=tokens.index(cword)
        expected=sorted([(tokens.index(h),tokens.index(v) if v else None,tokens.index(p)) for h,v,p in expected_words],key=str)
        outputs={arm:infer(tokens,predicates,marker,child,adapter,**options) for arm,options in ARMS.items()}
        assert signature(outputs['constituent_nonfinite_declared_frames'])==expected,(name,signature(outputs['constituent_nonfinite_declared_frames']),expected)
        controlled.append(dict(name=name,tokens=tokens,predicates=predicates,marker=marker,child=child,expected_chains=expected,outputs=outputs))
    dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json');rows=[]
    for i,s in enumerate(dev):
        pred=next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted'))
        gold={int(m):v['target'] for m,v in s['markers'].items() if v['kind']=='relative'}
        predicted={m['position']:m['target'] for m in pred['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None}
        for mode,scopes in [('reference_scope',gold),('predicted_scope',predicted)]:
            for bounded in (False,True):
                for marker in sorted(set(gold)|set(scopes)):
                    child=scopes.get(marker)
                    for arm,options in ARMS.items():
                        output=({'status':'missing_scope','parents':[],'antecedents':[],'chains':[]} if child is None else
                            infer(s['tokens'],s['finite'],marker,child,adapter,scopes=tuple(scopes.items()),
                                boundaries=s['boundaries'] if bounded else (),**options))
                        rows.append(dict(stream=i,mode=mode,boundaries='reference' if bounded else 'hidden',
                            marker=marker,child=child,reference_child=gold.get(marker),reference_parent=s['parents'].get(str(gold.get(marker))),
                            scope_correct=marker in gold and child==gold[marker],baseline_parent=pred['parents'].get(str(child)),arm=arm,result=output))
    OUT.mkdir(parents=True)
    save(OUT/'controlled.json',controlled);save(OUT/'predictions.json',rows)
    words=sorted({w for s in dev for w in s['tokens']}|{w for c in controlled for w in c['tokens']})
    save(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in words})
    inputs=[NINE/'development-truth.json',TEN/'predictions.json',RESERVE,
        Path(__file__),Path('src/voynich_smt/relative_constituents.py'),Path('src/voynich_smt/relative_bridge.py')]
    save(OUT/'manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'lexicon_resource':adapter.analyzer.resource,'arms':ARMS,'radius':16,
        'scope':'No new fitting; all 66 previously inspected development streams; supplied finite positions in all arms.',
        'heldout':'200 reserved sentences remain unscored','elapsed_seconds':time.monotonic()-start})
    print(f'{len(controlled)} controlled probes passed; {len(rows)} natural conditions saved in {time.monotonic()-start:.2f}s')

if __name__=='__main__':run()
