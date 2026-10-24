"""One bounded training-only hierarchical lag smoothing comparison."""
import argparse
from collections import Counter,defaultdict
import json
import math
from pathlib import Path
from statistics import mean
from benchmarks import long_range_realistic as prior
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/long-range-pooled')
CALIBRATION=(38001,38002)
SEEDS=(38011,38012,38013)
NULLS=(38101,38102,38103)
CANDIDATES=tuple((s,w) for s in (10,50,200) for w in (.25,.75))


def fit(data):
    model=prior.fit(data); pooled=defaultdict(Counter)
    for r in data:
        for d,v in r['lags'].items(): pooled[(d,v)][r['target']]+=1
    model['pooled']=pooled; return model


def evaluate(train,held,spec):
    strength,weight=spec; model=fit(train); scored=[]
    for r in held:
        target=r['target']; c=model['global']; p=(c[target]+.5)/(sum(c.values())+13)
        for c in (model['position'][r['pos']],model['immediate'][r['pos']+'|'+r['previous']]):
            p=(c[target]+20*p)/(sum(c.values())+20)
        baseline=-math.log2(p); probabilities={}
        for d,v in r['lags'].items():
            pool=model['pooled'][(d,v)]; pooled=(pool[target]+strength*p)/(sum(pool.values())+strength)
            fine=model['lag'][d+'|'+r['pos']+'|'+r['previous']+'|'+v]
            q=(fine[target]+strength*pooled)/(sum(fine.values())+strength)
            probabilities[d]=(1-weight)*p+weight*q
        mixture=-math.log2(mean(probabilities.values())); losses={d:-math.log2(q) for d,q in probabilities.items()}
        scored.append({'baseline':baseline,'mixture':mixture,'lags':losses})
    return {'gain':mean(r['baseline']-r['mixture'] for r in scored),'loss':mean(r['mixture'] for r in scored),'lag_gains':{str(d):mean(r['baseline']-r['lags'][str(d)] for r in scored) for d in prior.LAGS},'rows':scored}


def prepare():
    p={'code_sha256':digest(Path(__file__).read_text()),'generator_code_sha256':digest(Path(prior.__file__).read_text()),'null_code_sha256':digest(Path(prior.prior.__file__).read_text()),'calibration_seeds':CALIBRATION,'evaluation_seeds':SEEDS,'nulls':NULLS,'candidates':CANDIDATES,
       'scope':'Reuse frozen synthetic26letter uneven sparse generator and line-reset features. Hierarchical eachlag/value pooledcounts back off baseline then fineposition/length/immediate/lag context backs off pooled; blend withbaseline. Six fixedstrength/weight candidates. Select minimum balancedkind mean CV mixtureloss over two calibration seeds, first16trainblocks fit next16validate. Evaluation32train/89heldoutblocks new3seeds. No evaluation choice or lagselection. Compare frozen old estimator pairedon samefixtures, three conditionalfeature refittednulls eachmodel. Descriptive success criterion minweak excess > max independent/local/statecontrol excess; otherwise close branch. No pvalue/power/historical interpretation.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'selection':'training-only' if i==2 else False}; write_json(OUT/f'plan-{i}.json',plan); r={'plan':plan,'cases':{}}
    if i==2:
        r['calibration']={}
        for seed in CALIBRATION:
            for kind in prior.KINDS:
                blocks=prior.generate(seed,kind,'train'); a,b=prior.rows(blocks[:16]),prior.rows(blocks[16:])
                r['calibration'][f'{kind}-{seed}']={'train':a,'validation':b,'scores':{f'{s}-{w}':evaluate(a,b,(s,w)) for s,w in CANDIDATES}}
        r['cv_losses']={f'{s}-{w}':mean(c['scores'][f'{s}-{w}']['loss'] for c in r['calibration'].values()) for s,w in CANDIDATES}
        r['selected']=list(min(CANDIDATES,key=lambda spec:(r['cv_losses'][f'{spec[0]}-{spec[1]}'],spec)))
        print('Training selection',r['selected'],r['cv_losses'],flush=True)
    if 3<=i<=5:
        spec=json.loads((OUT/'iteration-2.json').read_text())['selected']; seed=SEEDS[i-3]
        for kind in prior.KINDS:
            blocks=[prior.generate(seed,kind,split) for split in ('train','heldout')]; a,b=map(prior.rows,blocks)
            r['cases'][f'{kind}-{seed}']={'blocks':blocks,'train':a,'heldout':b,'pooled':evaluate(a,b,spec),'old':prior.evaluate(a,b)}
    if i==6:
        spec=json.loads((OUT/'iteration-2.json').read_text())['selected']
        for j in range(3,6):
            for name,c in json.loads((OUT/f'iteration-{j}.json').read_text())['cases'].items():
                nulls={'pooled':[],'old':[]}
                for ns in NULLS:
                    a,b=[prior.prior.null_rows(c[split],f'{ns}:{split}') for split in ('train','heldout')]
                    nulls['pooled'].append(evaluate(a,b,spec)); nulls['old'].append(prior.evaluate(a,b))
                r['cases'][name]={model:{'nulls':scores,'excess':c[model]['gain']-mean(v['gain'] for v in scores)} for model,scores in nulls.items()}
    if i==7:
        nulls=json.loads((OUT/'iteration-6.json').read_text())['cases']; r['selected']=json.loads((OUT/'iteration-2.json').read_text())['selected']
        r['grouped']={kind:{model:[nulls[f'{kind}-{s}'][model]['excess'] for s in SEEDS] for model in ('pooled','old')} for kind in prior.KINDS}
        negatives=('independent','local','state-iid','state-local'); weak=r['grouped']['weak-lag4']['pooled']; control=[v for kind in negatives for v in r['grouped'][kind]['pooled']]
        r['criterion']={'min_weak':min(weak),'max_control':max(control),'separated':min(weak)>max(control),'scope':'Descriptive preset comparison, no fitted threshold or significance.'}
        r['decision']='Calibration passed descriptive separation; consider independent realistic replication before realtext.' if r['criterion']['separated'] else 'Close weak-long-range branch at this budget; no manuscript application or further estimator tuning.'
        print(json.dumps({k:r[k] for k in ('grouped','criterion','decision')}),flush=True)
    write_json(path,r); print('Stage',i,flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    else: prepare()
