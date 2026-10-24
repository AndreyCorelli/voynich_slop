"""Frozen pooled estimator tested on mapped-copy and stronger confound families."""
import argparse
import json
from pathlib import Path
import random
from statistics import mean
from benchmarks import long_range_pooled as estimator
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/long-range-families')
SEEDS=(39001,39002,39003)
NULLS=(39101,39102,39103)
KINDS=('independent','mapped-local','mapped-lag4','mapped-lag8','weak-mapped-lag4','persistent-state','template')


def generate(seed,kind,split):
    rng=random.Random(f'{seed}:{kind}:{split}'); alphabet=estimator.prior.ALPHABET
    perm=list(alphabet); random.Random(f'{seed}:mapping').shuffle(perm); mapping=dict(zip(alphabet,perm)); blocks=[]
    for n in range(32 if split=='train' else 89):
        words=[]; states=[]; phases=[]; operations=[]; positions=[]; lines=[]
        for line in range(2):
            state=rng.randrange(2); offset=rng.randrange(4)
            for pos in range(16):
                if rng.random()<.02: state=1-state
                phase=(pos+offset)%4; weights=[1/(i+1)**1.2 for i in range(26)]
                if kind=='persistent-state': weights=[(1 if (i<13)==(state==0) else .2)/(i%13+1)**1.2 for i in range(26)]
                final=rng.choices(alphabet,weights)[0]; initial=rng.choices(alphabet,weights)[0]; op='noise'; u=rng.random()
                if kind=='template':
                    # Fixed noisy phase emissions, no predecessor lookup.
                    if rng.random()<.7: final='aein'[phase]
                    if rng.random()<.7: initial='rtos'[phase]
                    op='template'
                if 'mapped' in kind:
                    lag=1 if kind=='mapped-local' else 8 if kind=='mapped-lag8' else 4
                    dose=.25 if kind.startswith('weak') else .6
                    if pos>=lag and u<dose: initial=mapping[words[-lag][-1]]; op=f'mapped{lag}'
                middle=rng.choices(('a','e','in','er','us'),(8,5,3,2,1))[0]
                words.append(initial+middle+final); states.append(state); phases.append(phase); operations.append(op); positions.append(pos); lines.append(line)
        blocks.append({'words':words,'states':states,'phases':phases,'operations':operations,'positions':positions,'lines':lines})
    return blocks,mapping


def rows(blocks,oracle=None):
    data=estimator.prior.rows(blocks)
    if oracle:
        labels=[b['states'][i] if oracle=='state' else b['phases'][i] for b in blocks for i in range(32) if b['positions'][i]>=8]
        data=[{**r,'pos':r['pos']+f':{oracle}{label}'} for r,label in zip(data,labels,strict=True)]
    return data


def prepare():
    selected=json.loads((estimator.OUT/'iteration-2.json').read_text()); spec=selected['selected']
    p={'code_sha256':digest(Path(__file__).read_text()),'estimator_code_sha256':digest(Path(estimator.__file__).read_text()),'selection_sha256':digest(selected),'spec':spec,'seeds':SEEDS,'nulls':NULLS,'kinds':KINDS,
       'scope':'Frozen pooledstrength/weight from earliertrainingcalibration; no newselection. New family seededalphabetpermutation mappedlag4/8 .6 weaklag4 .25 mappedlocal.6. Persistentlatentstate switches.02, stateemissionleakage.2; noisy4phase template first/final .7 prescribed phaseemissions no distantlookup. Independentunevencontrol. Same32train89evalblocks, artificial16wordlines/lengths, allsevenlagsmixture. Oraclecurrentstate/phase diagnostic bothconfounds all3seeds. Three conditionalfeature refittednulls. Criterion minweak excess > max independent/local/state/template control excess; descriptive only. No classifierthreshold, significance, historicalsource or manuscript experiment.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'selection':False}; write_json(OUT/f'plan-{i}.json',plan); r={'plan':plan,'cases':{}}
    if 2<=i<=4:
        seed=SEEDS[i-2]
        for kind in KINDS:
            pairs=[generate(seed,kind,s) for s in ('train','heldout')]; blocks=[a for a,b in pairs]; assert pairs[0][1]==pairs[1][1]
            a,b=map(rows,blocks); r['cases'][f'{kind}-{seed}']={'train':a,'heldout':b,'blocks':blocks,'mapping':pairs[0][1],'score':estimator.evaluate(a,b,p['spec'])}
    if i==5:
        for seed in SEEDS:
            for kind,oracle in (('persistent-state','state'),('template','phase')):
                pairs=[generate(seed,kind,s) for s in ('train','heldout')]; blocks=[a for a,b in pairs]; a,b=[rows(z,oracle) for z in blocks]
                r['cases'][f'oracle-{kind}-{seed}']={'train':a,'heldout':b,'blocks':blocks,'mapping':pairs[0][1],'oracle':oracle,'score':estimator.evaluate(a,b,p['spec'])}
    if i==6:
        for j in range(2,6):
            for name,c in json.loads((OUT/f'iteration-{j}.json').read_text())['cases'].items():
                controls=[estimator.evaluate(estimator.prior.prior.null_rows(c['train'],f'{ns}:train'),estimator.prior.prior.null_rows(c['heldout'],f'{ns}:heldout'),p['spec']) for ns in NULLS]
                r['cases'][name]={'nulls':controls,'excess':c['score']['gain']-mean(z['gain'] for z in controls)}
    if i==7:
        nulls=json.loads((OUT/'iteration-6.json').read_text())['cases']; r['grouped']={k:[nulls[f'{k}-{s}']['excess'] for s in SEEDS] for k in KINDS}
        r['oracle']={k:[nulls[f'oracle-{k}-{s}']['excess'] for s in SEEDS] for k in ('persistent-state','template')}
        minimum=min(r['grouped']['weak-mapped-lag4']); maximum=max(v for k in ('independent','mapped-local','persistent-state','template') for v in r['grouped'][k])
        r['criterion']={'min_weak':minimum,'max_control':maximum,'separated':minimum>maximum}
        r['decision']='Independentfamily descriptive separation passed; mechanism inference remains unproven.' if minimum>maximum else 'Specificity failed across families; stop estimator tuning and do not use this statistic as manuscript mechanism discriminator.'
        print(json.dumps({k:r[k] for k in ('grouped','oracle','criterion','decision')}),flush=True)
    write_json(path,r); print('Stage',i,flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    else: prepare()
