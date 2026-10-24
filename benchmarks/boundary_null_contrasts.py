"""Seven-stage matched refitted null contrasts and preset weaker known mechanisms."""
import argparse
import json
from pathlib import Path
from statistics import mean
from benchmarks import boundary_mechanisms as prior
from benchmarks import character_prediction as pred
from benchmarks.weak_boundary_calibration import reorder, stream_seed
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/boundary-null-contrasts')
SEEDS=(32001,32002,32003)
NULL_SEEDS=(32101,32102,32103)
DOSES=(.0625,.125)


def name(kind,dose,seed): return f'{kind}-{dose:g}-{seed}'


def prepare():
    base=prior.prepare(); source=pred.prepare(); natural=prior.prose_prepare()['cases']['german-113']; cases={}; families={}
    for seed in SEEDS:
        for dose in DOSES:
            for kind in ('encoder','generator'):
                n=name(kind,dose,seed); case={'kind':kind,'dose':dose,'seed':seed,'keys':{}}
                for split,template in (('train',source['development']),('heldout',source['heldout'])):
                    if kind=='encoder': case[split],case['keys'][split]=prior.encoder(natural[split],seed,dose,split=split)
                    else: case[split]=prior.generate(source['development'],template,base['mapping'],dose,stream_seed(seed,split))
                cases[n]=case; families[n]={'active':n,'nulls':[]}
                for ns in NULL_SEEDS:
                    null=n+f'-shuffle-{ns}'; cases[null]={'kind':'shuffle','parent':n,'null_seed':ns,**{split:reorder(case[split],0,stream_seed(ns,split))[0] for split in ('train','heldout')}}; families[n]['nulls'].append(null)
    old_nulls={}
    for kind in ('encoder','generator'):
        n=f'{kind}-null-31001'; original=base['cases'][n]; old_nulls[n]=[]
        for ns in NULL_SEEDS:
            null=n+f'-shuffle-{ns}'; cases[null]={'kind':'shuffle','parent':n,'null_seed':ns,**{split:reorder(original[split],0,stream_seed(ns,split))[0] for split in ('train','heldout')}}; old_nulls[n].append(null)
    active=lambda dose,seeds:[name(kind,dose,s) for s in seeds for kind in ('encoder','generator')]
    with_nulls=lambda names:[item for n in names for item in [n]+families[n]['nulls']]
    stages={'1':[n for names in old_nulls.values() for n in names],'2':[name('encoder',d,SEEDS[0]) for d in DOSES],
            '3':[name('generator',d,SEEDS[0]) for d in DOSES],'4':[n for d in DOSES for kind in ('encoder','generator') for n in families[name(kind,d,SEEDS[0])]['nulls']],
            '5':with_nulls(active(.125,SEEDS[1:])),'6':with_nulls(active(.0625,SEEDS[1:])),'7':[]}
    p={'prior_sha256':digest(base),'spec':base['spec'],'cases':cases,'families':families,'old_nulls':old_nulls,'stages':stages,
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(prior.__file__),Path(pred.__file__),Path('benchmarks/weak_boundary_calibration.py'))},
       'scope':'Preset weaker doses1/16,1/8; encoder deterministic public schedule, generator preference probabilities, not equal strengths. Three keys/streams per dose/kind, three independently seeded refitted word shuffles each. Exact folio/position-bin/length inventories, every slot length and baseline losses preserved within each pair. Earlier mechanism-specific nulls also compared against3refittedshuffles. Original old-null scores reused, newactive/newnull scores refitted. No model/dose selection, classifier, historical ranking or target-based tuning. Structure shared descriptive protocol; generator vocabulary advantage unchanged. Surrogates can retain position/length effects; contrasts measure removed ordering, not every dependence.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def contrasts(p,results):
    contrast={}
    for n,f in p['families'].items():
        if n not in results or any(v not in results for v in f['nulls']): continue
        actual=results[n]['gain_position']; nulls=[results[v]['gain_position'] for v in f['nulls']]
        contrast[n]={'active_gain':actual,'null_gains':nulls,'excess_over_mean_null':actual-mean(nulls),'exceeds_all_three_nulls':actual>max(nulls)}
    return contrast


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'cases':p['stages'][str(i)],'selection':False}; write_json(OUT/f'plan-{i}.json',plan)
    results={n:pred.aggregate(pred.evaluate(p['cases'][n]['train'],p['cases'][n]['heldout'],p['spec'])) for n in plan['cases']}
    assessments={1:'Old mechanism-specific nulls checked against exact-inventory refitted shuffles; next weaker encoder schedules.',2:'Preset weak encoder schedules scored; next corresponding generator probabilities.',3:'Weak generators scored; next three matched null streams per fixture.',4:'Seed32001 matched contrasts available; replicate preset1/8fixtures.',5:'Three1/8key/stream contrasts complete; replicate1/16fixtures.',6:'All weak fixtures and matched contrasts complete; summarize structural differences without classifier fitting.',7:'Matched excess gains and descriptive structure frozen; judge whether either statistic identifies a mechanism.'}
    r={'plan':plan,'results':results,'summary':{n:summarize(v) for n,v in results.items()},'assessment':assessments[i]}
    if i==7:
        all_results={n:v for stage in range(1,7) for n,v in json.loads((OUT/f'iteration-{stage}.json').read_text())['results'].items()}
        r['contrasts']=contrasts(p,all_results); r['structure']={n:prior.structure(p['cases'][n]['heldout']) for n in p['families']}
        old=json.loads((prior.OUT/'iteration-4.json').read_text())['results']
        r['old_null_contrasts']={n:{'original_gain':old[n]['gain_position'],'matched_shuffle_gains':[all_results[v]['gain_position'] for v in names],'excess_over_mean_null':old[n]['gain_position']-mean(all_results[v]['gain_position'] for v in names)} for n,names in p['old_nulls'].items()}
    write_json(path,r); print(i,r['assessment'],json.dumps({n:round(v['gain_position_per_character'],6) for n,v in r['summary'].items()}),flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(args.iteration)
    else: prepare()
