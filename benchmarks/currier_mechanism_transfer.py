"""Frozen source-transfer and out-of-grid rejection audit."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import random
from statistics import mean
from benchmarks import currier_mechanism_discrimination as prior
from benchmarks import currier_mechanism_comparison as base
from benchmarks import currier_alphabet_comparison as cipher
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/currier-mechanism-transfer')
SEEDS=(71001,71002,71003)
OUTSIDERS=('fixed-two','word-final-marker','glyph-shuffle','renewal-4','renewal-8')

def outsiders(payload,glyphs,seed):
    # Fixed two-glyph code for each mono symbol; no extra labels needed.
    doubled=[[tuple(x for g in w for x in (g,glyphs[-1])) for w in l] for l in payload]
    marked=[[tuple(w)+(glyphs[-1],) for w in l] for l in payload]
    stream=[g for l in payload for w in l for g in w];random.Random(seed).shuffle(stream)
    cursor=0;shuffled=[]
    for line in payload:
        words=[]
        for word in line:words.append(tuple(stream[cursor:cursor+len(word)]));cursor+=len(word)
        shuffled.append(words)
    return {'fixed-two':doubled,'word-final-marker':marked,'glyph-shuffle':shuffled,
            'renewal-4':base.resegment(payload,4,seed+1),'renewal-8':base.resegment(payload,8,seed+1)}

def prepare():
    old=json.loads((prior.OUT/'prepared.json').read_text());parent=json.loads(cipher.PARENT.read_text());selected={}
    for source,data in parent['sources'].items():
        stream=base.natural_stream(data)
        excluded=[(p['start'],p['end']) for p in parent['passages'][source]]
        excluded +=[(p['start'],p['end']) for ps in old['passages'][source].values() for p in ps]
        selected[source]=prior.passages(stream,len(stream)//2,len(stream),excluded,8)
    deps=[Path(__file__),Path(prior.__file__),Path(base.__file__),Path(cipher.__file__),Path('benchmarks/text_generation_comparison.py')]
    p={'prior_sha256':digest(old),'prior_public_sha256':digest(json.loads((prior.OUT/'public.json').read_text())),
       'parent_sha256':digest(parent),'passages':selected,'allocations':old['allocations'],'glyphs':old['glyphs'],'seeds':SEEDS,
       'code_sha256':{str(f):digest(f.read_text()) for f in deps},'source_sha256':old['source_sha256'],
       'protocol':'Reuse only prior training features/labels, frozen feature vector, centroid fit, LOPO training radius and margin0.2. Fresh evaluation64-word second-half passages excluding all earlier paired/discrimination passages;8per source,3new keys,4lines of16. Same25glyph codes/allocation. All six directed cross-source broad tests trained only mono versus renewal6; sparse preserved cases count as preserved broad, despite not entering broad training. Fine transfer Caesar->Aquinas and reverse uses4classes; German omitted due equivalent sparse arms. Five outside-grid generators: fixed2glyph expansion, deterministic final marker sharing payload alphabet (strip final symbol reversible with known rule), glyph shuffle preserving lengths/frequencies, mono renewal4/8. Renewal4/8 are parameter shifts, not outside renewal family. Evaluation labels hidden from predictor; public source routes transfer models only, no target fitting. Broad/fine known correctness and outsider acceptance/rejection separated; forced accuracy reported. No thresholds tuned; no Voynich or Z3.'}
    p=json.loads(json.dumps(p));path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p
    else:write_json(path,p)
    return p

def build(p):
    public=[];truth=[];groups=None
    for source,ps in p['passages'].items():
        labels=prior.CLASSES if len(p['allocations'][source]['mono'])<25 else ('mono','renewal-6')
        for i,passage in enumerate(ps):
            plain=base.layout(passage['words'],[16]*4)
            for seed in SEEDS:
                mono=cipher.key_for(p['allocations'][source]['mono'],p['glyphs'],seed)
                allocated=cipher.key_for(p['allocations'][source]['allocated'],p['glyphs'],seed)
                payload=cipher.encode(plain,mono,seed+10,'independent')
                profiles=outsiders(payload,p['glyphs'],seed+40)
                for label in labels:
                    encoder=allocated if label.startswith('sparse') else mono
                    lines=cipher.encode(plain,encoder,seed+10,'word-deterministic' if label=='sparse-deterministic' else 'independent')
                    profiles[label]=base.resegment(lines,6,seed+30) if label=='renewal-6' else lines
                for label,lines in profiles.items():
                    metrics=base.measure(lines);features,groups=prior.vector(metrics)
                    identity=digest([source,i,seed,label])[:24]
                    public.append({'id':identity,'source':source,'passage_index':i,'features':features})
                    truth.append({'id':identity,'source':source,'passage_index':i,'seed':seed,'label':label,'outside_grid':label in OUTSIDERS,'payload':lines,'mono_payload':payload,'metrics':metrics})
        print(source,'evaluation generated',flush=True)
    random.Random(72001).shuffle(public)
    training=json.loads((prior.OUT/'public.json').read_text())['records']
    write_json(OUT/'public.json',{'prepared_sha256':digest(p),'feature_groups':groups,'training':[r for r in training if r['split']=='training'],'evaluation':public})
    write_json(OUT/'truth.json',{'prepared_sha256':digest(p),'records':truth})

def predict():
    public=json.loads((OUT/'public.json').read_text());training=public['training'];groups=public['feature_groups'];sources=sorted({r['source'] for r in training});models={};predictions=[]
    for source in sources:
        rows=[r for r in training if r['source']==source]
        broad=[{**r,'label':'preserved' if r['label']=='mono' else 'renewal-6'} for r in rows if r['label'] in ('mono','renewal-6')]
        models[source+'-broad']=prior.fit(broad,groups)
        if source!='german-113':models[source+'-fine']=prior.fit(rows,groups)
    for case in public['evaluation']:
        for source in sources:
            if source==case['source']:continue
            for mode in ('broad','fine'):
                key=source+'-'+mode
                if key not in models or (mode=='fine' and case['source']=='german-113'):continue
                predictions.append({'id':case['id'],'training_source':source,'mode':mode,**prior.classify(case['features'],models[key],groups)})
    write_json(OUT/'predictions.json',{'prepared_sha256':public['prepared_sha256'],'models':models,'predictions':predictions})

def score():
    public=json.loads((OUT/'public.json').read_text());truth=json.loads((OUT/'truth.json').read_text());pred=json.loads((OUT/'predictions.json').read_text());labels={r['id']:r for r in truth['records']};groups=defaultdict(list)
    for r in pred['predictions']:
        t=labels[r['id']];groups[r['mode'],r['training_source'],t['source'],t['outside_grid']].append((t,r))
    summary=[]
    for (mode,train,test,outside),rows in sorted(groups.items()):
        def target(t):return ('preserved' if t['label']!='renewal-6' else 'renewal-6') if mode=='broad' and not outside else t['label']
        accepted=[(t,r) for t,r in rows if r['prediction']!='unresolved']
        confusion=Counter((t['label'],r['prediction']) for t,r in rows)
        summary.append({'mode':mode,'training_source':train,'evaluation_source':test,'outside_grid':outside,'cases':len(rows),'accepted':len(accepted),'coverage':len(accepted)/len(rows),
         'accepted_accuracy':mean(target(t)==r['prediction'] for t,r in accepted) if accepted and not outside else None,
         'forced_accuracy':mean(target(t)==r['nearest'] for t,r in rows) if not outside else None,
         'outside_rejection_rate':1-len(accepted)/len(rows) if outside else None,
         'confusion':[[y,k,n] for (y,k),n in sorted(confusion.items())]})
    write_json(OUT/'report.json',{'prepared_sha256':public['prepared_sha256'],'predictions_sha256':digest(pred),'generated_cases':len(truth['records']),'predictions':len(pred['predictions']),'summary':summary,'complete':True,'solver_calls':0})
    for r in summary:print(r['mode'],r['training_source'],'->',r['evaluation_source'],'outside',r['outside_grid'],'coverage',round(r['coverage'],3),'accuracy',r['accepted_accuracy'],flush=True)

def run():p=prepare();build(p);predict();score()
if __name__=='__main__':run()
