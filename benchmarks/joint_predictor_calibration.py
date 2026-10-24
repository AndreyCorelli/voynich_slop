"""Training-only bounded joint-generator calibration with frozen character predictor."""
import argparse
import copy
import json
import random
from pathlib import Path
from statistics import mean
from benchmarks import joint_order_constraints as joint
from benchmarks import character_prediction as pred
from benchmarks.weak_boundary_calibration import reorder, stream_seed
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/joint-predictor-calibration')
RATES=(0,.125,.5,1)
SEEDS=(35001,35002,35003)
NULLS=(35101,35102,35103)


def blend(avoid,mapped,rate,seed):
    rng=random.Random(seed)
    return [copy.deepcopy(z if rng.random()<rate else a) for a,z in zip(avoid,mapped,strict=True)]


def score(train,held,spec,nulls):
    active=pred.aggregate(pred.evaluate(train,held,spec)); controls=[]
    for seed in nulls:
        a=reorder(train,0,stream_seed(seed,'train'))[0]; b=reorder(held,0,stream_seed(seed,'heldout'))[0]
        controls.append(pred.aggregate(pred.evaluate(a,b,spec)))
    return {'active':active,'nulls':controls,'excess':active['gain_position']-mean(c['gain_position'] for c in controls)}


def prepare():
    base,_=joint.prepare(); selection=json.loads((pred.OUT/'iteration-6.json').read_text()); spec=selection['specs'][selection['selected']]
    p={'base_sha256':digest(base),'spec':spec,'rates':RATES,'seeds':SEEDS,'nulls':NULLS,'code_sha256':digest(Path(__file__).read_text()),
       'scope':'Four prior middle excerpts, previously scored direct statistics but not this predictor comparison. First16trainingblocks fit calibration mapping/models, next16 calibrate rate. Fixed four-rate blockwise mixture of beam16 avoidance and joint optimization. Choose rate nearest prose matched-null excess, one calibration key/null. Refit mapping on all32trainingblocks after freezing rates. Evaluate89heldoutblocks with3presetkeys and3refittednulls. No heldout rate choice, new independent corpus claim, historical mechanism inference or manuscript scoring.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return base,p


def encoded_pair(a,b,seed):
    return [joint.prior.encoding.encoder(blocks,seed,.0625,split=split)[0] for blocks,split in ((a,'train'),(b,'heldout'))]


def run(i):
    base,p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'stage':'freeze' if i==1 else 'training-only-calibration' if i==2 else 'evaluation' if i<7 else 'assessment'}
    write_json(OUT/f'plan-{i}.json',plan); r={'plan':plan}
    if i==2:
        r['calibration']={}
        for source,data in base['sources'].items():
            a,b=data['training'][:16],data['training'][16:]; mapping,_=joint.prior.mapped.training_mapping(a)
            target=score(*encoded_pair(a,b,SEEDS[0]),p['spec'],NULLS[:1]); candidates={}; variants=[]
            for split,blocks in (('train',a),('heldout',b)):
                variants.append((joint.optimize(blocks,mapping,stream_seed(SEEDS[0],split),False),joint.optimize(blocks,mapping,stream_seed(SEEDS[0],split),True)))
            for rate in RATES:
                payload=[blend(*pair,rate,stream_seed(SEEDS[0],split+'-mix')) for pair,split in zip(variants,('train','heldout'))]
                candidates[str(rate)]=score(*encoded_pair(*payload,SEEDS[0]),p['spec'],NULLS[:1])
            chosen=min(RATES,key=lambda rate:(abs(candidates[str(rate)]['excess']-target['excess']),rate))
            r['calibration'][source]={'target':target,'candidates':candidates,'selected_rate':chosen}
            print('Calibrated',source,chosen,'target',target['excess'],flush=True)
    if 3<=i<=6:
        source=joint.prior.SOURCES[i-3]; data=base['sources'][source]; rate=json.loads((OUT/'iteration-2.json').read_text())['calibration'][source]['selected_rate']; r.update(source=source,rate=rate,results={})
        for seed in SEEDS:
            payload=[]
            for split,blocks in (('train',data['training']),('heldout',data['heldout'])):
                a=joint.optimize(blocks,data['mapping'],stream_seed(seed,split),False); b=joint.optimize(blocks,data['mapping'],stream_seed(seed,split),True)
                payload.append(blend(a,b,rate,stream_seed(seed,split+'-mix')))
            for kind,pair in (('prose',(data['training'],data['heldout'])),('calibrated',payload)):
                result=score(*encoded_pair(*pair,seed),p['spec'],NULLS)
                encoded=encoded_pair(*pair,seed)[1]
                result['repeat']=joint.prior.summarize(encoded)['adjusted']; result['payload']=pair
                r['results'][f'{kind}-{seed}']=result
                print(source,kind,seed,'excess',round(result['excess'],6),'repeat',round(result['repeat'],6),flush=True)
    if i==7:
        r['grouped']={}
        for j in range(3,7):
            row=json.loads((OUT/f'iteration-{j}.json').read_text())
            r['grouped'][row['source']]={'rate':row['rate'],**{kind:{metric:mean(row['results'][f'{kind}-{seed}'][metric] for seed in SEEDS) for metric in ('excess','repeat')} for kind in ('prose','calibrated')}}
        r['assessment']='Assess fixed training-selected rates on heldout; signs alone insufficient. Same inspected excerpts, no independent mechanism classification. Stop local-feature tuning after this bounded loop.'
        print(json.dumps(r['grouped']),flush=True)
    write_json(path,r); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): run(i)
    else: prepare()
