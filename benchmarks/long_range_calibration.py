"""Seven-stage conditional longer-range predictor calibration on synthetic controls."""
import argparse
from collections import Counter,defaultdict
import copy
import json
import math
from pathlib import Path
import random
from statistics import mean
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/long-range-calibration')
ALPHABET='abcd'
LAGS=tuple(range(2,9))
SEEDS=(36001,36002,36003)
NULLS=(36101,36102,36103)
KINDS=('independent','local','lag2','lag4','lag8','mixed')
STRENGTH=20


def generate(seed,kind,split,weak=False):
    rng=random.Random(f'{seed}:{kind}:{split}:{weak}'); blocks=[]
    for n in range(128 if split=='train' else 256):
        words=[]
        for i in range(32):
            # Independent final letters prevent a lag signal arising solely
            # through a chain of adjacent initial/final dependencies.
            final=rng.choice(ALPHABET); initial=rng.choice(ALPHABET); u=rng.random()
            dose=.25 if weak else .8
            if kind=='local' and i>=1 and u<dose: initial=words[i-1][-1]
            if kind.startswith('lag'):
                lag=int(kind[3:])
                if i>=lag and u<dose: initial=words[i-lag][-1]
            if kind=='mixed':
                if i>=1 and u<dose/2: initial=words[i-1][-1]
                elif i>=4 and u<dose: initial=words[i-4][-1]
            words.append(initial+rng.choice(ALPHABET)+final)
        blocks.append(words)
    return blocks


def rows(blocks):
    return [{'pos':'early' if i<16 else 'late','previous':b[i-1][-1],'lags':{str(d):b[i-d][-1] for d in LAGS},'target':b[i][0]} for b in blocks for i in range(8,32)]


def fit(data):
    globalcounts=Counter(r['target'] for r in data); position=defaultdict(Counter); immediate=defaultdict(Counter); lagcounts=defaultdict(Counter)
    for r in data:
        position[r['pos']][r['target']]+=1; immediate[r['pos']+'|'+r['previous']][r['target']]+=1
        for d,v in r['lags'].items(): lagcounts[d+'|'+r['pos']+'|'+r['previous']+'|'+v][r['target']]+=1
    return {'global':globalcounts,'position':position,'immediate':immediate,'lag':lagcounts}


def probabilities(model,r):
    base={c:(model['global'][c]+.5)/(sum(model['global'].values())+2) for c in ALPHABET}
    for counts in (model['position'][r['pos']],model['immediate'][r['pos']+'|'+r['previous']]):
        base={c:(counts[c]+STRENGTH*base[c])/(sum(counts.values())+STRENGTH) for c in ALPHABET}
    extended={}
    for d,v in r['lags'].items():
        counts=model['lag'][d+'|'+r['pos']+'|'+r['previous']+'|'+v]
        extended[d]={c:(counts[c]+STRENGTH*base[c])/(sum(counts.values())+STRENGTH) for c in ALPHABET}
    return base,extended


def evaluate(train,held):
    model=fit(train); scored=[]
    for r in held:
        base,extensions=probabilities(model,r); target=r['target']
        baseline=-math.log2(base[target]); losses={d:-math.log2(p[target]) for d,p in extensions.items()}
        mixture=-math.log2(mean(p[target] for p in extensions.values()))
        scored.append({'baseline':baseline,'mixture':mixture,'lags':losses})
    return {'gain':mean(r['baseline']-r['mixture'] for r in scored),'lag_gains':{str(d):mean(r['baseline']-r['lags'][str(d)] for r in scored) for d in LAGS},'rows':scored}


def null_rows(data,seed):
    rng=random.Random(seed); result=copy.deepcopy(data); groups=defaultdict(list)
    for i,r in enumerate(data): groups[(r['pos'],r['previous'])].append(i)
    for indices in groups.values():
        for d in LAGS:
            values=[data[i]['lags'][str(d)] for i in indices]; rng.shuffle(values)
            for i,v in zip(indices,values): result[i]['lags'][str(d)]=v
    return result


def transform(data):
    mapping=dict(zip(ALPHABET,'dcba'))
    return [{**r,'previous':mapping[r['previous']],'target':mapping[r['target']],'lags':{d:mapping[v] for d,v in r['lags'].items()}} for r in data]


def prepare():
    p={'code_sha256':digest(Path(__file__).read_text()),'seeds':SEEDS,'nulls':NULLS,'lags':LAGS,'kinds':KINDS,'strength':STRENGTH,
       'scope':'Ideal synthetic four-symbol, three-letter words; final letters independently sampled. Local or planted2/4/8lag initial dependencies, strong.8 weak.25; mixedhalf local/half lag4. Train128blocks/eval256blocks of32words, score only positions8..31. Position early/late + immediate-final smoothed baseline. Eachlag jointconditional extension backs off baseline, arithmetic7lag probability mixture frozen. No lag/modelselection. Conditional null independently permutes each lagfeature within position/immediate groups in training and evaluation and refits model; target/position/immediate unchanged. Null rows need not reconstruct a coherent text. No corpus/manuscript scoring or historical inference.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'selection':False}
    write_json(OUT/f'plan-{i}.json',plan); result={'plan':plan,'cases':{}}
    if 2<=i<=4:
        seed=SEEDS[i-2]
        for kind in KINDS:
            a,b=[rows(generate(seed,kind,split)) for split in ('train','heldout')]
            result['cases'][f'{kind}-{seed}']={'train':a,'heldout':b,'score':evaluate(a,b)}
    if i==5:
        for kind in KINDS:
            a,b=[rows(generate(SEEDS[0],kind,split,True)) for split in ('train','heldout')]
            score=evaluate(a,b); renamed=evaluate(transform(a),transform(b))
            assert abs(score['gain']-renamed['gain'])<1e-12
            result['cases'][f'weak-{kind}']={'train':a,'heldout':b,'score':score,'renamed_score':renamed}
    if i==6:
        for stage in range(2,6):
            prior=json.loads((OUT/f'iteration-{stage}.json').read_text())
            for name,c in prior['cases'].items():
                controls=[evaluate(null_rows(c['train'],f'{ns}:train'),null_rows(c['heldout'],f'{ns}:heldout')) for ns in NULLS]
                result['cases'][name]={'nulls':controls,'excess':c['score']['gain']-mean(v['gain'] for v in controls)}
    if i==7:
        nulls=json.loads((OUT/'iteration-6.json').read_text())['cases']
        result['grouped']={k:{'gains':[json.loads((OUT/f'iteration-{j}.json').read_text())['cases'][f'{k}-{SEEDS[j-2]}']['score']['gain'] for j in range(2,5)],'excesses':[nulls[f'{k}-{s}']['excess'] for s in SEEDS]} for k in KINDS}
        result['weak']={k:nulls[f'weak-{k}']['excess'] for k in KINDS}
        result['assessment']='Control calibration only; positive versus local-only specificity must precede real-text application. No classifier threshold or manuscript conclusion.'
        print(json.dumps(result['grouped']),json.dumps(result['weak']),flush=True)
    write_json(path,result); print('Stage',i,{n:round(c.get('score',{}).get('gain',c.get('excess',0)),6) for n,c in result['cases'].items()},flush=True)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    else: prepare()
