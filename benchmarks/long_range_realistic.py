"""Sparse 26-symbol and shared-state calibration; synthetic only."""
import argparse
from collections import Counter,defaultdict
import copy
import json
import math
from pathlib import Path
import random
import string
from statistics import mean
from benchmarks import long_range_calibration as prior
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/long-range-realistic')
ALPHABET=string.ascii_lowercase
KINDS=('independent','local','lag4','lag8','weak-lag4','state-iid','state-local')
SEEDS=(37001,37002,37003)
NULLS=(37101,37102,37103)
LAGS=prior.LAGS
STRENGTH=20


def generate(seed,kind,split,large=False):
    rng=random.Random(f'{seed}:{kind}:{split}:{large}'); blocks=[]
    for n in range((128 if large else 32) if split=='train' else 89):
        words=[]; states=[]; positions=[]; lines=[]
        for line in range(2):
            state=rng.randrange(2)
            for pos in range(16):
                if rng.random()<.1: state=1-state
                weights=[1/(i+1)**1.2 for i in range(26)]
                if kind.startswith('state'):
                    weights=[(1 if (i<13)==(state==0) else .08)/(i%13+1)**1.2 for i in range(26)]
                final=rng.choices(ALPHABET,weights)[0]; initial=rng.choices(ALPHABET,weights)[0]; u=rng.random()
                if kind in ('local','state-local') and pos and u<.6: initial=words[-1][-1]
                if 'lag' in kind:
                    lag=8 if kind=='lag8' else 4; dose=.25 if kind.startswith('weak') else .6
                    if pos>=lag and u<dose: initial=words[-lag][-1]
                middle=rng.choices(('a','e','in','er','us'),(8,5,3,2,1))[0]
                words.append(initial+middle+final); states.append(state); positions.append(pos); lines.append(line)
        blocks.append({'words':words,'states':states,'positions':positions,'lines':lines})
    return blocks


def rows(blocks,oracle=False):
    output=[]
    for b in blocks:
        for i,w in enumerate(b['words']):
            if b['positions'][i]<8: continue
            assert all(b['lines'][i-d]==b['lines'][i] for d in LAGS)
            context=f"{int(b['positions'][i]>=12)}:{len(w)}"+(f":state{b['states'][i]}" if oracle else '')
            output.append({'pos':context,'previous':b['words'][i-1][-1],'target':w[0],'lags':{str(d):b['words'][i-d][-1] for d in LAGS}})
    return output


def fit(data): return prior.fit(data)


def evaluate(train,held):
    model=fit(train); scored=[]
    for r in held:
        target=r['target']; globalcounts=model['global']; p=(globalcounts[target]+.5)/(sum(globalcounts.values())+13)
        for counts in (model['position'][r['pos']],model['immediate'][r['pos']+'|'+r['previous']]):
            p=(counts[target]+STRENGTH*p)/(sum(counts.values())+STRENGTH)
        baseline=-math.log2(p); probs={}
        for d,v in r['lags'].items():
            c=model['lag'][d+'|'+r['pos']+'|'+r['previous']+'|'+v]
            probs[d]=(c[target]+STRENGTH*p)/(sum(c.values())+STRENGTH)
        mixture=-math.log2(mean(probs.values())); losses={d:-math.log2(q) for d,q in probs.items()}
        scored.append({'baseline':baseline,'mixture':mixture,'lags':losses})
    return {'gain':mean(r['baseline']-r['mixture'] for r in scored),'lag_gains':{str(d):mean(r['baseline']-r['lags'][str(d)] for r in scored) for d in LAGS},'rows':scored}


def prepare():
    p={'code_sha256':digest(Path(__file__).read_text()),'prior_code_sha256':digest(Path(prior.__file__).read_text()),'seeds':SEEDS,'nulls':NULLS,'kinds':KINDS,'strength':20,'lags':LAGS,
       'scope':'Synthetic26letter Zipf1.2 emissions, variable3/4letterwords finite5middleforms, artificial16wordlines. Train32blocks1024words score512events; eval89blocks2848words score1424events. Baselinepositionhalfline + currentwordlength + immediatefinal; fixedstrength20, uniform.5prior. Stronglagcopy.6 weak.25 local.6. Two latent emissionstates switch.1 eachword resetlines, stateiid/local no explicitdistantcopy. Oracle exposes generatingstate via baselinecontext. Predetermined largertrain128blocks check. Equal7lagprobabilitymixture, no lag/smoothingselection. Conditional feature nulls refitted, no coherenttext/permutationpvalue. No realcorpus/manuscript run.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'selection':False}; write_json(OUT/f'plan-{i}.json',plan)
    r={'plan':plan,'cases':{}}
    if 2<=i<=4:
        seed=SEEDS[i-2]
        for kind in KINDS:
            blocks=[generate(seed,kind,s) for s in ('train','heldout')]; a,b=map(rows,blocks)
            r['cases'][f'{kind}-{seed}']={'train':a,'heldout':b,'blocks':blocks,'score':evaluate(a,b)}
    if i==5:
        for kind in ('state-iid','state-local'):
            for seed in SEEDS:
                blocks=[generate(seed,kind,s) for s in ('train','heldout')]; a,b=[rows(z,True) for z in blocks]
                r['cases'][f'oracle-{kind}-{seed}']={'train':a,'heldout':b,'blocks':blocks,'score':evaluate(a,b)}
        for kind in ('local','weak-lag4','state-local'):
            blocks=[generate(SEEDS[0],kind,'train',True),generate(SEEDS[0],kind,'heldout')]; a,b=map(rows,blocks)
            r['cases'][f'large-{kind}']={'train':a,'heldout':b,'blocks':blocks,'score':evaluate(a,b)}
    if i==6:
        for j in range(2,6):
            for name,c in json.loads((OUT/f'iteration-{j}.json').read_text())['cases'].items():
                controls=[evaluate(prior.null_rows(c['train'],f'{ns}:train'),prior.null_rows(c['heldout'],f'{ns}:heldout')) for ns in NULLS]
                r['cases'][name]={'nulls':controls,'excess':c['score']['gain']-mean(n['gain'] for n in controls)}
    if i==7:
        nulls=json.loads((OUT/'iteration-6.json').read_text())['cases']; r['grouped']={kind:[nulls[f'{kind}-{s}']['excess'] for s in SEEDS] for kind in KINDS}
        r['oracle']={kind:[nulls[f'oracle-{kind}-{s}']['excess'] for s in SEEDS] for kind in ('state-iid','state-local')}
        r['large']={kind:nulls[f'large-{kind}']['excess'] for kind in ('local','weak-lag4','state-local')}
        r['assessment']='Evaluate sparsity and latent-state confounding before manuscript use; longer-range predictive association does not imply a direct distant mechanism.'
        print(json.dumps({k:r[k] for k in ('grouped','oracle','large')}),flush=True)
    write_json(path,r); print('Stage',i,{n:round(c.get('score',{}).get('gain',c.get('excess',0)),6) for n,c in r['cases'].items()},flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    else: prepare()
