"""Seven-stage exact constrained-frequency-adjusted adjacency source-order test."""
import argparse
from collections import Counter,defaultdict
import copy
import itertools
import json
from pathlib import Path
import random
from statistics import mean
from benchmarks import historical_word_lengths as historical
from benchmarks import multilingual_character as corpus
from benchmarks import character_prediction as pred
from benchmarks import boundary_mechanisms as encoding
from benchmarks import mapped_boundary_calibration as mapped
from benchmarks.weak_boundary_calibration import stream_seed
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/adjacent-order-replication')
SEEDS=(34001,34002,34003)
SOURCES=('german-113','german-133','german-253','italian')
KINDS=('prose','random','mapped','repeat','avoid')


def poolkey(b,i): return (pred.prior.position_bin(b['positions'][i],4),len(b['words'][i]))


def order(blocks,kind,mapping,seed):
    if kind=='prose': return copy.deepcopy(blocks)
    rng=random.Random(seed); out=copy.deepcopy(blocks)
    for b in out:
        pools=defaultdict(list)
        for i,w in enumerate(b['words']): pools[poolkey(b,i)].append(list(w))
        for i,w in enumerate(b['words']):
            pool=pools[poolkey(b,i)]; candidates=list(range(len(pool)))
            if i:
                if kind=='mapped' and b['line_ids'][i]==b['line_ids'][i-1] and rng.random()<.5:
                    preferred=[j for j,v in enumerate(pool) if v[0]==mapping.get(b['words'][i-1][-1])]
                    if preferred: candidates=preferred
                elif kind=='repeat':
                    preferred=[j for j,v in enumerate(pool) if v==b['words'][i-1]]
                    if preferred: candidates=preferred
                elif kind=='avoid':
                    preferred=[j for j,v in enumerate(pool) if v!=b['words'][i-1]]
                    if preferred: candidates=preferred
            b['words'][i]=pool.pop(rng.choice(candidates))
    return out


def measure(b):
    counts=defaultdict(Counter)
    for i,w in enumerate(b['words']): counts[poolkey(b,i)][''.join(w)]+=1
    rows=[]
    for i in range(1,len(b['words'])):
        a=poolkey(b,i-1); z=poolkey(b,i); ca=counts[a]; cz=counts[z]; na=sum(ca.values()); nz=sum(cz.values())
        expected=sum(c*(c-1) for c in ca.values())/(na*(na-1)) if a==z else sum(ca[w]*cz[w] for w in ca)/(na*nz)
        rows.append({'observed':int(b['words'][i]==b['words'][i-1]),'expected':expected,'within':b['line_ids'][i]==b['line_ids'][i-1]})
    within=[r for r in rows if r['within']]
    return {'observed_repeat':mean(r['observed'] for r in rows),'expected_repeat':mean(r['expected'] for r in rows),'adjusted':mean(r['observed']-r['expected'] for r in rows),
            'within_adjusted':mean(r['observed']-r['expected'] for r in within) if within else None,'edges':rows}


def summarize(blocks):
    rows=[measure(b) for b in blocks]
    return {k:mean(r[k] for r in rows if r[k] is not None) for k in ('observed_repeat','expected_repeat','adjusted','within_adjusted')}|{'blocks':len(rows),'rows':rows}


def prepare():
    prior=corpus.prepare(); template=pred.prepare(); german={n:(seg,meta) for n,seg,meta in historical.german_sources()}; cases={}; sources={}
    for source in SOURCES:
        segments,metadata=historical.italian_segments() if source=='italian' else german[source]
        blocks,coverage=corpus.blocks32(segments)
        # For already-scored works, middle121blocks avoids both first121 and last121.
        chosen=blocks[:121] if source=='german-253' else blocks[121:242]
        assert len(chosen)==121
        if source!='german-253': assert 242<=len(blocks)-121
        training=corpus.assign(template['development'],chosen[:32]); heldout=corpus.assign(template['heldout'],chosen[32:]); mapping,audit=mapped.training_mapping(training)
        sources[source]={'metadata':metadata,'coverage':coverage,'training':training,'heldout':heldout,'mapping':mapping,'mapping_audit':audit}
        for seed in SEEDS:
            for kind in KINDS:
                name=f'{source}-{kind}-{seed}'; payload=order(heldout,kind,mapping,stream_seed(seed,'heldout'))
                encoded,key=encoding.encoder(payload,seed,.0625,split='heldout'); cases[name]={'source':source,'kind':kind,'seed':seed,'payload':payload,'encoded':encoded,'key':key}
    stage=lambda selected:[n for n,c in cases.items() if c['source'] in selected]
    stages={'1':[],'2':stage(('german-113',)),'3':stage(('german-133',)),'4':stage(('german-253',)),'5':stage(('italian',)),'6':[],'7':[]}
    p={'corpus_sha256':digest(prior),'sources':sources,'cases':cases,'stages':stages,
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(historical.__file__),Path(encoding.__file__),Path(pred.__file__))},
       'feature':'Per32wordblock adjacent exact-repeat fraction minus analytic expectation under uniform permutation within position-bin/length pools. Same pool uses without-replacement probability; distinct pools independent hypergeometric allocations. Primaryalladjacent31edges, companionwithin-line edges. Block-equal means. Separately payload and commonencoded representation.',
       'scope':'Preset four sources/3seeds/5ordering types. Previously unscored blocks for this statistical branch; descriptive corpuswide audits saw them. Train32blocks derive source mapping; eval89blocks never overlapping prior statistical primary/tail blocks for three repeated works. German253new source for this predictor branch. Prose original order; uniform permutation; mapped.5; greedy repeat preference; greedy repeat avoidance. All evaluation inventories/public slot lengths given to generators, no lexical invention. Common1/16encodingkeys/schedule. Avoid-generator is deliberate hard negative, not historical model. Exact feature frozen before evaluating new excerpts. No classifier threshold, manuscript scoring, predictive refits, Z3, or mechanism posterior.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'cases':p['stages'][str(i)],'selection':False}; write_json(OUT/f'plan-{i}.json',plan)
    results={n:{rep:summarize(p['cases'][n][rep]) for rep in ('payload','encoded')} for n in plan['cases']}
    assessment={1:'Feature and4source excerpts frozen; exact uniform-permutation expectation test precedes real-data evaluation.',2:'Disjoint German113 excerpt scored across5orders; next German133.',3:'Disjoint German133 scored; next new German253 source.',4:'New German253 source scored; next disjoint Italian excerpt.',5:'Italian scored; test candidate specificity against deliberate repeat-avoidance generator.',6:'Hard-negative overlaps documented; no universal prose/generation discriminator.',7:'Frozen feature assessed on all sources; retain source-order insight without manuscript mechanism classification.'}[i]
    r={'plan':plan,'results':results,'assessment':assessment}
    if i==1:
        example={'words':[list(w) for w in ('a','a','b','b')],'positions':[4]*4,'line_ids':['x']*4}; expected=measure(example)['expected_repeat']
        permutations=list(itertools.permutations(example['words'])); actual=mean(measure({**example,'words':list(words)})['observed_repeat'] for words in permutations)
        assert abs(expected-actual)<1e-12; r['exhaustive_null_check']=True
    if i in (6,7):
        allresults={n:v for j in range(2,6) for n,v in json.loads((OUT/f'iteration-{j}.json').read_text())['results'].items()}
        r['grouped']={s:{kind:{rep:mean(allresults[f'{s}-{kind}-{seed}'][rep]['adjusted'] for seed in SEEDS) for rep in ('payload','encoded')} for kind in KINDS} for s in SOURCES}
    write_json(path,r); print(i,assessment,json.dumps({n:round(v['encoded']['adjusted'],6) for n,v in results.items()}),flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    else: prepare()
