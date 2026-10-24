"""Seven-stage known reversible encoding versus local word-generation fixtures."""
import argparse
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
import random
import string
from statistics import mean
from benchmarks import character_prediction as pred
from benchmarks.multilingual_character import prepare as prose_prepare
from benchmarks.mapped_boundary_calibration import training_mapping
from benchmarks.weak_boundary_calibration import reorder, stream_seed
from benchmarks.character_calibration import summarize
from benchmarks.text_generation_comparison import metrics
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/boundary-mechanisms')
SEEDS=(31001,31002,31003)


def encoder(blocks,seed,dose,null=False,split='train'):
    rng=random.Random(seed); alphabet=list(string.ascii_lowercase); payload=alphabet[:]; rng.shuffle(payload); marker=alphabet[:]; rng.shuffle(marker)
    code=dict(zip(alphabet,payload)); marks=dict(zip(alphabet,marker)); out=copy.deepcopy(blocks); noise=random.Random(stream_seed(seed,split))
    for b in out:
        for i,w in enumerate(b['words']):
            encoded=[code[c] for c in w]
            # A public deterministic position schedule, reset at each block.
            if i and b['line_ids'][i]==b['line_ids'][i-1] and i%int(1/dose)==0:
                encoded=[noise.choice(alphabet) if null else marks[b['words'][i-1][-1]]]+encoded
            b['words'][i]=encoded
    return out,{'payload':code,'marker':marks,'dose':dose,'null':null}


def decode(blocks,key):
    inverse={c:p for p,c in key['payload'].items()}; out=copy.deepcopy(blocks)
    for block_index,b in enumerate(out):
        for i,w in enumerate(b['words']):
            marked=i and b['line_ids'][i]==b['line_ids'][i-1] and i%int(1/key['dose'])==0
            if marked:
                if not key['null']: assert w[0]==key['marker'][blocks[block_index]['words'][i-1][-1]]
                w=w[1:]
            b['words'][i]=[inverse[c] for c in w]
    return out


def generate(training,template,mapping,dose,seed):
    rng=random.Random(seed); pools=defaultdict(list)
    for b in training:
        for n,w in zip(b['positions'],b['words']): pools[pred.prior.position_bin(n,4)].append(list(w))
    fallback=[w for b in training for w in b['words']]; out=copy.deepcopy(template)
    for b in out:
        for i in range(len(b['words'])):
            pool=pools.get(pred.prior.position_bin(b['positions'][i],4),fallback)
            if i and b['line_ids'][i]==b['line_ids'][i-1] and rng.random()<dose:
                target=mapping.get(b['words'][i-1][-1]); matched=[w for w in pool if w[0]==target]
                if matched: pool=matched
            b['words'][i]=list(rng.choice(pool))
    return out


def prepare():
    source=pred.prepare(); prose=prose_prepare(); natural=prose['cases']['german-113']; mapping,audit=training_mapping(source['development']); selection=json.loads((pred.OUT/'iteration-6.json').read_text()); cases={}
    for dose in (.25,.5):
        for seed in SEEDS:
            for kind in ('encoder','generator'):
                name=f'{kind}-{dose:g}-{seed}'; case={'kind':kind,'dose':dose,'seed':seed,'keys':{}}
                for split,template in (('train',source['development']),('heldout',source['heldout'])):
                    if kind=='encoder': case[split],case['keys'][split]=encoder(natural[split],seed,dose,split=split)
                    else: case[split]=generate(source['development'],template,mapping,dose,stream_seed(seed,split))
                cases[name]=case
    for kind in ('encoder','generator'):
        name=f'{kind}-null-31001'; case={'kind':kind+'-null','dose':.25,'seed':31001,'keys':{}}
        for split,template in (('train',source['development']),('heldout',source['heldout'])):
            if kind=='encoder': case[split],case['keys'][split]=encoder(natural[split],31001,.25,null=True,split=split)
            else: case[split]=generate(source['development'],template,mapping,0,stream_seed(31001,split))
        cases[name]=case
    stages={'1':[],'2':['encoder-0.25-31001'],'3':['generator-0.25-31001'],'4':['encoder-null-31001','generator-null-31001'],
            '5':[f'{kind}-0.25-{seed}' for seed in SEEDS[1:] for kind in ('encoder','generator')],
            '6':[f'{kind}-0.5-{seed}' for seed in SEEDS for kind in ('encoder','generator')],'7':[]}
    p={'prior_sha256':digest(source),'prose_sha256':digest(prose),'selection_sha256':digest(selection),'spec':selection['specs'][selection['selected']], 'mapping':mapping,'cases':cases,'stages':stages,'reference_blocks':source['heldout'],
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(pred.__file__),Path('benchmarks/text_generation_comparison.py'))},
       'scope':'Synthetic known mechanisms, not historical hypotheses. Encoder: fixed bijective26letter payload key plus one scheduled prefix determined by previous output final label, public within-line block-position schedule1/4 or1/2, decode strips scheduled prefix and inverts key. Null uses random prefixes on same schedule. Generator: sample exact development words with replacement by position bin, probabilistically prefer training-only mapped initial conditional on previous final label. Different seed per split; no evaluation spellings/lengths enter generator beyond32wordlayout slots. No contraction, encoder expands by at most1unit/word. Both1024train2848heldwords, same slots/alphabet; lengths, vocabularies, fitted symbol mappings and novelty differ. Encoder plaintext German113 primary cached excerpt. Refitted frozen predictor; no model selection. Structural metrics descriptive, not likelihood or classifier. Generator knows manuscript vocabulary; encoder does not. No Z3/language inference.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def structure(blocks):
    rows=[metrics([tuple(w) for w in b['words']]) for b in blocks]
    return {k:mean(r[k] for r in rows) for k in rows[0]}


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'cases':p['stages'][str(i)],'selection':False}; write_json(OUT/f'plan-{i}.json',plan)
    results={n:pred.aggregate(pred.evaluate(p['cases'][n]['train'],p['cases'][n]['heldout'],p['spec'])) for n in plan['cases']}
    assessment={1:'Fixtures and public schedules frozen; verify reversible construction before scoring.',2:'Quarter-schedule encoding scored; next quarter-strength generation.',3:'Quarter-strength generator scored; next mechanism-specific nulls.',4:'Nulls scored; replicate quarter fixtures with new keys/streams.',5:'Quarter replications scored; test preset half-strength fixtures.',6:'Half-strength fixtures scored; compare structural metrics without fitting a mechanism classifier.',7:'Structural contrasts recorded: frozen suffix gain is compared separately from length/spelling/repetition; no historical ranking.'}[i]
    r={'plan':plan,'results':results,'summary':{n:summarize(result) for n,result in results.items()},'assessment':assessment}
    if i==1:
        natural=prose_prepare()['cases']['german-113']
        for name,case in p['cases'].items():
            if case['kind'].startswith('encoder'):
                for split in ('train','heldout'): assert [b['words'] for b in decode(case[split],case['keys'][split])]==[b['words'] for b in natural[split]]
        r['reversibility_passed']=True
    if i==7: r['structure']={'manuscript':structure(p['reference_blocks']),**{n:structure(case['heldout']) for n,case in p['cases'].items()}}
    write_json(path,r); print(i,assessment,json.dumps(r['summary']),flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(i=args.iteration)
    else: prepare()
