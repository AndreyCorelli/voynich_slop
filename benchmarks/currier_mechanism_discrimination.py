"""Fresh-passage synthetic discrimination; truth withheld during prediction."""
from collections import Counter,defaultdict
import json
import math
from pathlib import Path
import random
from statistics import mean
from benchmarks import currier_mechanism_comparison as base
from benchmarks import currier_alphabet_comparison as cipher
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/currier-mechanism-discrimination')
SIZES={'training':8,'calibration':4,'evaluation':8}
SEEDS={'training':(61001,61002,61003),'calibration':(62001,62002,62003),'evaluation':(63001,63002,63003)}
CLASSES=('mono','sparse-independent','sparse-deterministic','renewal-6')
MARGIN=.2

def vector(m):
    # Four groups receive equal total weight: lengths, repetition/variants,
    # adjacency, position. Histogram and moment terms share the length group.
    result=[];groups=[]
    def add(xs,g):result.extend(xs);groups.extend([g]*len(xs))
    for kind in ('token','type'):
        hist=m[kind+'_lengths'];total=sum(hist.values())
        add([sum(n for k,n in hist.items() if int(k)==i)/total for i in range(1,17)]+[sum(n for k,n in hist.items() if int(k)>16)/total],0)
        add([m[kind+'_moments'][k] for k in ('mean','variance','skewness')],0)
    add([m[k] for k in ('repeated_token_fraction','repeat_pair_fraction','near_variant_token_pair_fraction','near_variant_type_pair_fraction')],1)
    add([m[k] for k in ('adjacent_length_correlation','adjacent_repeat_fraction')],2)
    for kind in ('word','line'):
        add([m['position'][kind]['mutual_information_bits']],3)
        # Frequency-rank bin concentration retains position shape without labels.
        add([sum(v for k,v in b.items() if int(k)<3) for b in m['position'][kind]['rank_profiles']],3)
    return result,groups

def passages(stream,lo,hi,excluded,count):
    found=[];cursor=lo
    while len(found)<count:
        words,start,end=base.take_passage(stream,cursor,64)
        assert end<=hi,'Insufficient fresh source material'
        overlap=[b for a,b in excluded if a<end and b>start]
        if overlap:cursor=max(overlap);continue
        found.append({'words':words,'start':start,'end':end});cursor=end
    return found

def prepare():
    parent=json.loads(cipher.PARENT.read_text())
    deps=[Path(__file__),Path(cipher.__file__),Path(base.__file__),Path('benchmarks/text_generation_comparison.py')]
    selected={};allocations={}
    for source,data in parent['sources'].items():
        stream=base.natural_stream(data);half=len(stream)//2
        excluded=[(p['start'],p['end']) for p in parent['passages'][source]]
        first=passages(stream,0,half,excluded,12);second=passages(stream,half,len(stream),excluded,8)
        selected[source]={'training':first[:8],'calibration':first[8:],'evaluation':second}
        alphabet=sorted({u for w in stream if w for u in w})
        counts=Counter(u for p in first[:8] for w in p['words'] for u in w)
        allocations[source]={kind:cipher.allocation(alphabet,counts,25,kind=='allocated') for kind in ('mono','allocated')}
    p={'parent_sha256':digest(parent),'passages':selected,'allocations':allocations,'seeds':SEEDS,'sizes':SIZES,'glyphs':parent['glyphs'],
       'code_sha256':{str(f):digest(f.read_text()) for f in deps},'source_sha256':parent['source_sha256'],
       'protocol':'Fresh nonoverlapping64-word real-source passages excluding all earlier paired passages.8training/4calibration/8evaluation per source,3fresh split-specific keys;4lines of16 original words conditioned geometry. Mono,25-label sparse independent,25-label sparse word-deterministic,mono-payload renewal mean6. German sparse classes omitted as exactly equivalent mono. Source identity public; classifiers source-specific, source/language inference not tested. All four feature groups equal weight; training mean imputation and standardization, nearest class centroid. Reject if relative nearest-centroid margin<0.2 or distance exceeds training95th percentile leave-one-passage-out true-class distance. Threshold frozen; calibration descriptive only. Predictions saved without calibration/evaluation labels, then truth scored. No Voynich scoring, nulls, expansions, contractions, learned codegroups or Z3.'}
    p=json.loads(json.dumps(p));path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p
    else:write_json(path,p)
    return p

def build(p):
    public=[];truth={};records=[]
    for source,splits in p['passages'].items():
        classes=CLASSES if len(p['allocations'][source]['mono'])<25 else ('mono','renewal-6')
        for split,ps in splits.items():
            for i,passage in enumerate(ps):
                plain=base.layout(passage['words'],[16]*4)
                for seed in p['seeds'][split]:
                    mono=cipher.key_for(p['allocations'][source]['mono'],p['glyphs'],seed)
                    allocated=cipher.key_for(p['allocations'][source]['allocated'],p['glyphs'],seed)
                    for label in classes:
                        encoder=allocated if label.startswith('sparse') else mono
                        mode='word-deterministic' if label=='sparse-deterministic' else 'independent'
                        payload=cipher.encode(plain,encoder,seed+10,mode)
                        lines=base.resegment(payload,6,seed+30) if label=='renewal-6' else payload
                        metrics=base.measure(lines);features,groups=vector(metrics)
                        identity=digest([source,split,i,seed,label])[:24]
                        item={'id':identity,'source':source,'split':split,'passage_index':i,'features':features}
                        if split=='training':item['label']=label
                        public.append(item);truth[identity]=label
                        records.append({'id':identity,'source':source,'split':split,'passage_index':i,'seed':seed,'label':label,'payload':lines,'metrics':metrics,'codebook':encoder.codebook})
            print(source,split,'generated',flush=True)
    rng=random.Random(64001);rng.shuffle(public)
    write_json(OUT/'public.json',{'prepared_sha256':digest(p),'feature_groups':groups,'records':public})
    write_json(OUT/'truth.json',{'prepared_sha256':digest(p),'labels':truth,'records':records})

def standardizer(rows):
    dim=len(rows[0]['features']);centers=[];scales=[]
    for j in range(dim):
        xs=[r['features'][j] for r in rows if r['features'][j] is not None]
        center=mean(xs) if xs else 0
        scale=math.sqrt(mean((x-center)**2 for x in xs)) if xs else 0
        centers.append(center);scales.append(scale if scale>1e-10 else 1)
    return centers,scales

def transformed(row,centers,scales):return [(x-c)/s if x is not None else 0 for x,c,s in zip(row['features'],centers,scales)]
def distance(a,b,groups):
    return mean(mean((x-y)**2 for x,y,g in zip(a,b,groups) if g==group) for group in sorted(set(groups)))
def centroid(xs):return [mean(values) for values in zip(*xs)]
def quantile95(xs):return sorted(xs)[math.ceil(.95*len(xs))-1]

def fit(rows,groups):
    centers,scales=standardizer(rows);vectors={r['id']:transformed(r,centers,scales) for r in rows}
    labels=sorted({r['label'] for r in rows})
    centroids={label:centroid([vectors[r['id']] for r in rows if r['label']==label]) for label in labels}
    radii={}
    # Refit scaling and centroid with the entire held-out passage removed,
    # preventing its other key draws/paired mechanisms from entering the fold.
    for label in labels:
        ds=[]
        for index in sorted({r['passage_index'] for r in rows}):
            keep=[r for r in rows if r['passage_index']!=index];c,s=standardizer(keep)
            target=centroid([transformed(r,c,s) for r in keep if r['label']==label])
            ds.extend(distance(transformed(r,c,s),target,groups) for r in rows if r['passage_index']==index and r['label']==label)
        radii[label]=quantile95(ds)
    return {'centers':centers,'scales':scales,'centroids':centroids,'radii':radii}

def classify(features,model,groups):
    row={'features':features};v=transformed(row,model['centers'],model['scales'])
    ranked=sorted((distance(v,c,groups),label) for label,c in model['centroids'].items())
    first,label=ranked[0];second=ranked[1][0];margin=(second-first)/second if second else 0
    prediction=label if margin>=MARGIN and first<=model['radii'][label] else 'unresolved'
    return {'prediction':prediction,'nearest':label,'margin':margin,'distance':first,'radius':model['radii'][label]}

def predict():
    # Only this public file is read; evaluation/calibration truth is absent.
    public=json.loads((OUT/'public.json').read_text());rows=public['records'];groups=public['feature_groups']
    models={s:fit([r for r in rows if r['source']==s and r['split']=='training'],groups) for s in sorted({r['source'] for r in rows})}
    predictions=[{'id':r['id'],**classify(r['features'],models[r['source']],groups)} for r in rows if r['split']!='training']
    write_json(OUT/'predictions.json',{'prepared_sha256':public['prepared_sha256'],'models':models,'predictions':predictions})

def score():
    public=json.loads((OUT/'public.json').read_text());truth=json.loads((OUT/'truth.json').read_text());pred=json.loads((OUT/'predictions.json').read_text())
    byid={r['id']:r for r in public['records']};groups=defaultdict(list)
    for r in pred['predictions']:
        case=byid[r['id']];groups[case['source'],case['split']].append((truth['labels'][r['id']],r))
    summary=[]
    for (source,split),rs in sorted(groups.items()):
        accepted=[(y,r) for y,r in rs if r['prediction']!='unresolved'];confusion=Counter((y,r['prediction']) for y,r in rs)
        summary.append({'source':source,'split':split,'cases':len(rs),'passages':len({byid[r['id']]['passage_index'] for _,r in rs}),
         'accepted':len(accepted),'coverage':len(accepted)/len(rs),'accepted_accuracy':mean(y==r['prediction'] for y,r in accepted) if accepted else None,
         'forced_accuracy':mean(y==r['nearest'] for y,r in rs),'correct_overall':sum(y==r['prediction'] for y,r in rs)/len(rs),
         'confusion':[[y,k,n] for (y,k),n in sorted(confusion.items())]})
    write_json(OUT/'report.json',{'prepared_sha256':public['prepared_sha256'],'prediction_sha256':digest(pred),'summary':summary,'complete':True,'solver_calls':0})
    for s in summary:print(s['source'],s['split'],'coverage',round(s['coverage'],3),'accepted_accuracy',s['accepted_accuracy'],'forced',round(s['forced_accuracy'],3),flush=True)

def run():
    p=prepare();build(p);predict();score()
if __name__=='__main__':run()
