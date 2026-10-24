"""Seven-stage word-inventory-preserving boundary-dependence calibration."""
import argparse
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
import random
from statistics import mean
from benchmarks import character_prediction as pred
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/weak-boundary-calibration')
SEEDS=(27001,27002,27003)
RATES=(0,.25,.5,1)


def stream_seed(seed,split):
    return int(hashlib.sha256(f'{seed}:{split}'.encode()).hexdigest()[:16],16)


def reorder(blocks,rate,seed):
    out=copy.deepcopy(blocks); pools=defaultdict(list); rng=random.Random(seed)
    for b in blocks:
        for w,n in zip(b['words'],b['positions']): pools[(b['folio'],pred.prior.position_bin(n,4),len(w))].append(list(w))
    stats={'eligible':0,'attempted':0,'available_matches':0,'matched':0}
    for b in out:
        for i,w in enumerate(b['words']):
            pool=pools[(b['folio'],pred.prior.position_bin(b['positions'][i],4),len(w))]
            attempt=rng.random()<rate; candidates=list(range(len(pool)))
            if i and b['line_ids'][i]==b['line_ids'][i-1]:
                stats['eligible']+=1; matching=[j for j,v in enumerate(pool) if v[0]==b['words'][i-1][-1]]
                stats['available_matches']+=bool(matching)
                if attempt:
                    stats['attempted']+=1
                    if matching: candidates=matching
            chosen=rng.choice(candidates); b['words'][i]=pool.pop(chosen)
            if i and b['line_ids'][i]==b['line_ids'][i-1]: stats['matched']+=b['words'][i][0]==b['words'][i-1][-1]
    assert all(not pool for pool in pools.values()); return out,stats


def name(seed,rate): return f'seed-{seed}-rate-{rate:g}'


def prepare():
    source=pred.prepare(); selection=json.loads((pred.OUT/'iteration-6.json').read_text()); cases={}
    for seed in SEEDS:
        for rate in RATES:
            case={'seed':seed,'rate':rate,'streams':{split:stream_seed(seed,split) for split in ('train','heldout')},'stats':{}}
            for split,key in (('train','development'),('heldout','heldout')): case[split],case['stats'][split]=reorder(source[key],rate,case['streams'][split])
            cases[name(seed,rate)]=case
    stages={'1':[name(s,0) for s in SEEDS],'2':[name(SEEDS[0],.25)],'3':[name(SEEDS[0],.5)],'4':[name(SEEDS[0],1)],
            '5':[name(s,.25) for s in SEEDS[1:]],'6':[name(s,.5) for s in SEEDS[1:]],'7':[name(s,1) for s in SEEDS[1:]]}
    p={'prior_sha256':digest(source),'selection_sha256':digest(selection),'spec':selection['specs'][selection['selected']], 'cases':cases,'stages':stages,
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(pred.__file__))},
       'scope':'No model selection. All cases shuffle exact words within folio/position-bin/length pools, preserving every slot length, layout, and per-folio word inventory in each split. At eligible within-line transitions favor words starting with preceding output final unit with preset probability0/.25/.5/1 when available; fallback uniform. Random draws and candidate depletion mean rates are not realized matching rates. Train/test RNG streams independently seeded. Same random seeds pair rates, not identical random trajectories. Strongest attainable dependence limited by inventory; no glyph mutation. Refit fixed predictor and baseline in each case. Only3 realizations per dose, no power estimate or historical mechanism inference. Reused manuscript corpus, no fresh-text replication.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'cases':p['stages'][str(i)],'selection':False}
    write_json(OUT/f'plan-{i}.json',plan)
    results={n:pred.aggregate(pred.evaluate(p['cases'][n]['train'],p['cases'][n]['heldout'],p['spec'])) for n in plan['cases']}
    assessment={1:'Independent-stream inventory-preserving nulls scored; proceed to preset weak dose.',2:'Weak dose scored; next middle dose, without selecting on results.',3:'Middle dose scored; next maximum feasible matching.',4:'Maximum feasible dose scored; replicate weak dose on two further streams.',5:'Weak-dose replication scored; replicate middle dose.',6:'Middle-dose replication scored; finish maximum-dose replication.',7:'Three realizations per dose complete; compare dose response and constraints, without claiming detection power.'}[i]
    result={'plan':plan,'results':results,'summary':{n:summarize(r) for n,r in results.items()},'assessment':assessment}; write_json(path,result); print(i,assessment,json.dumps(result['summary']),flush=True); return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(args.iteration)
    else: prepare()
