"""Frozen seven-stage joint ordering-constraint stress test; no solver calls."""
import argparse
import copy
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from benchmarks import adjacent_order_replication as prior
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/joint-order-constraints')
KINDS=('prose','random','avoid','beam-avoid','beam-joint')
WIDTH=16


def optimize(blocks,mapping,seed,joint):
    rng=random.Random(seed); output=copy.deepcopy(blocks)
    for b in output:
        pools=defaultdict(Counter)
        for i,w in enumerate(b['words']): pools[prior.poolkey(b,i)][''.join(w)]+=1
        # Lexicographic objective: minimize repeats first, maximize mapped
        # within-line transitions second. Finite beam, not an optimum proof.
        states=[(0,0,rng.random(),[],dict(pools))]
        for i in range(len(b['words'])):
            key=prior.poolkey(b,i); expanded=[]
            for repeats,hits,_,sequence,remaining in states:
                for word,count in remaining[key].items():
                    if not count: continue
                    updated=remaining.copy(); updated[key]=remaining[key].copy(); updated[key][word]-=1
                    repeat=int(bool(sequence) and sequence[-1]==word)
                    hit=int(bool(sequence) and b['line_ids'][i]==b['line_ids'][i-1] and mapping.get(sequence[-1][-1])==word[0])
                    expanded.append((repeats+repeat,hits+hit,rng.random(),sequence+[word],updated))
            expanded.sort(key=lambda s:(s[0],-s[1] if joint else 0,s[2]))
            states=expanded[:WIDTH]
        b['words']=[list(w) for w in states[0][3]]
    return output


def boundary(block):
    pools=defaultdict(Counter)
    for i,w in enumerate(block['words']): pools[prior.poolkey(block,i)][''.join(w)]+=1
    return pools


def mapped_measure(blocks,mapping):
    values=[]
    for b in blocks:
        pools=boundary(b); rows=[]
        for i in range(1,len(b['words'])):
            if b['line_ids'][i]!=b['line_ids'][i-1]: continue
            a=prior.poolkey(b,i-1); z=prior.poolkey(b,i); ca=pools[a]; cz=pools[z]
            na=sum(ca.values()); nz=sum(cz.values())
            numerator=sum(n*(m-int(a==z and u==v)) for u,n in ca.items() for v,m in cz.items() if mapping.get(u[-1])==v[0])
            expected=numerator/(na*(nz-int(a==z)))
            observed=int(mapping.get(b['words'][i-1][-1])==b['words'][i][0])
            rows.append({'observed':observed,'expected':expected})
        values.append({'adjusted':mean(r['observed']-r['expected'] for r in rows),'rows':rows})
    return {'adjusted':mean(v['adjusted'] for v in values),'blocks':values}


def prepare():
    base=prior.prepare()
    p={'base_sha256':digest(base),'code_sha256':digest(Path(__file__).read_text()),'width':WIDTH,'kinds':KINDS,'seeds':prior.SEEDS,'sources':prior.SOURCES,
       'scope':'Same four previously scored excerpts, no new replication claim. Public per-block position/length inventories. Beam16 lexicographically minimizes exact repeats, then maximizes training-derived mapped within-line initial/final matches for joint arm. Random ties preset seeds. No global optimum claim. Payload mapped excess uses exact constrained permutation expectation; encoded repeat excess uses prior common encoder. No predictive refits or manuscript scoring. All arms frozen before scoring.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return base,p


def run(i):
    base,p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    source=prior.SOURCES[i-2] if 2<=i<=5 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'source':source,'selection':False}
    write_json(OUT/f'plan-{i}.json',plan); results={}
    if source:
        data=base['sources'][source]
        for seed in prior.SEEDS:
            for kind in KINDS:
                if kind.startswith('beam'):
                    payload=optimize(data['heldout'],data['mapping'],prior.stream_seed(seed,'heldout'),kind=='beam-joint')
                else: payload=base['cases'][f'{source}-{kind}-{seed}']['payload']
                encoded,key=prior.encoding.encoder(payload,seed,.0625,split='heldout')
                results[f'{kind}-{seed}']={'payload':payload,'encoded':encoded,'key':key,'repeat':prior.summarize(encoded),'mapped':mapped_measure(payload,data['mapping'])}
    result={'plan':plan,'results':results}
    if i in (6,7):
        grouped={}
        for j,s in enumerate(prior.SOURCES,2):
            rows=json.loads((OUT/f'iteration-{j}.json').read_text())['results']
            grouped[s]={k:{'repeat':mean(rows[f'{k}-{seed}']['repeat']['adjusted'] for seed in prior.SEEDS),'mapped':mean(rows[f'{k}-{seed}']['mapped']['adjusted'] for seed in prior.SEEDS)} for k in KINDS}
        result['grouped']=grouped
        result['assessment']='Joint constraints can be deliberately engineered; compare magnitude per source, not signs alone. No mechanism identification or global optimum claim.'
    write_json(path,result); print('Stage',i,source or 'freeze/assessment',json.dumps(result.get('grouped',{})),flush=True)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): run(i)
    else: prepare()
