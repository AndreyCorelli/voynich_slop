"""Seven-stage exact shared-inventory source-order comparison under common encoding."""
import argparse
import copy
import json
from pathlib import Path
from statistics import mean
from benchmarks import character_prediction as pred
from benchmarks import boundary_mechanisms as encoding
from benchmarks import mapped_boundary_calibration as mapped
from benchmarks.weak_boundary_calibration import reorder, stream_seed
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/shared-inventory-mechanisms')
SEEDS=(33001,33002,33003)
NULL_SEEDS=(33101,33102,33103)
SOURCES=('german-113','german-133')


def local_order(blocks,mapping,seed):
    proxy=copy.deepcopy(blocks)
    for b in proxy: b['folio']=f"{b['folio']}:{b['start']}"
    out,stats=mapped.reorder(proxy,.5,seed,mapping)
    for a,b in zip(blocks,out,strict=True): b['folio']=a['folio']
    return out,stats


def prepare():
    prose=encoding.prose_prepare(); selection=json.loads((pred.OUT/'iteration-6.json').read_text()); spec=selection['specs'][selection['selected']]; cases={}; mappings={}; payloads={}
    for source in SOURCES:
        original=prose['cases'][source]; mapping,audit=mapped.training_mapping(original['train']); mappings[source]={'mapping':mapping,'audit':audit}
        for seed in SEEDS:
            for kind in ('prose','local'):
                name=f'{source}-{kind}-{seed}'; case={'source':source,'kind':kind,'seed':seed,'keys':{},'ordering_stats':{}}
                for split in ('train','heldout'):
                    plain=original[split]
                    if kind=='local': plain,case['ordering_stats'][split]=local_order(plain,mapping,stream_seed(seed,split))
                    payloads[name+':'+split]=plain
                    case[split],case['keys'][split]=encoding.encoder(plain,seed,.0625,split=split)
                cases[name]=case
                for ns in NULL_SEEDS:
                    null=name+f'-shuffle-{ns}'; cases[null]={'kind':'shuffle','parent':name,'source':source,'null_seed':ns,
                        **{split:reorder(case[split],0,stream_seed(ns,split))[0] for split in ('train','heldout')}}
    names=lambda source,seeds:[f'{source}-{kind}-{seed}' for seed in seeds for kind in ('prose','local')]
    active=names(SOURCES[0],SEEDS)+names(SOURCES[1],SEEDS)
    stages={'1':[],'2':names(SOURCES[0],SEEDS[:1]),'3':names(SOURCES[0],SEEDS[1:]),'4':names(SOURCES[1],SEEDS),
            '5':[n for n,c in cases.items() if c['kind']=='shuffle'],'6':[],'7':[]}
    p={'prose_sha256':digest(prose),'selection_sha256':digest(selection),'spec':spec,'cases':cases,'payloads':payloads,'mappings':mappings,'stages':stages,'active':active,
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(encoding.__file__),Path(mapped.__file__),Path(pred.__file__))},
       'scope':'Equal public word inventories per block/position-bin/length, unchanged slot lengths and layout. Prose original order versus local conditional sampling without replacement, dose.5 training-only source-specific mapping. Common encoder keys and1/16marker schedule for both, prefix count and output slot lengths identical. Generator supplied each evaluation block inventory, not hidden text prediction; no unseen lexical generation. Exact payload vocabulary/frequencies shared across source types. Same representation means both outputs reversibly encode sequences: tests source-order distinction, not exclusive generation-versus-encoding causes. Two German sources,3keys/streams,3refitted nulls per case. No source/model/dose selection, classifier, historical inference or Z3.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'cases':p['stages'][str(i)],'selection':False}; write_json(OUT/f'plan-{i}.json',plan)
    results={n:pred.aggregate(pred.evaluate(p['cases'][n]['train'],p['cases'][n]['heldout'],p['spec'])) for n in plan['cases']}
    assessment={1:'Shared inventories and common reversible representation frozen and audited; score source113 first pair.',2:'First source-order pair scored; replicate keys and ordering streams.',3:'Source113 replicas scored; test preset second source133.',4:'Second source scored; compare3refittedinventorynulls per fixture.',5:'Matched nulls scored; inspect raw-payload versus encoded structural features.',6:'Structural contrasts recorded under equal vocabulary; no classifier fitted. Summarize paired source-order contrasts.',7:'Final paired assessment: conditional ordering and prose share representation and inventories; retain overlapping features and source differences.'}[i]
    r={'plan':plan,'results':results,'summary':{n:summarize(v) for n,v in results.items()},'assessment':assessment}
    if i==1:
        for n in p['active']:
            for split in ('train','heldout'): assert [b['words'] for b in encoding.decode(p['cases'][n][split],p['cases'][n]['keys'][split])]==[b['words'] for b in p['payloads'][n+':'+split]]
        r['roundtrip_passed']=True
    if i==6: r['structure']={n:{'payload':encoding.structure(p['payloads'][n+':heldout']),'encoded':encoding.structure(p['cases'][n]['heldout'])} for n in p['active']}
    if i==7:
        allresults={n:v for stage in range(1,6) for n,v in json.loads((OUT/f'iteration-{stage}.json').read_text())['results'].items()}; contrasts={}
        for n in p['active']:
            nulls=[allresults[n+f'-shuffle-{ns}']['gain_position'] for ns in NULL_SEEDS]
            contrasts[n]={'gain':allresults[n]['gain_position'],'null_gains':nulls,'excess':allresults[n]['gain_position']-mean(nulls)}
        r['contrasts']=contrasts; r['paired_excess_differences']={f'{s}-{seed}':contrasts[f'{s}-local-{seed}']['excess']-contrasts[f'{s}-prose-{seed}']['excess'] for s in SOURCES for seed in SEEDS}
    write_json(path,r); print(i,assessment,json.dumps({n:round(v['gain_position_per_character'],6) for n,v in r['summary'].items()}),flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    else: prepare()
