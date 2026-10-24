"""Seven-stage out-of-folio word prediction comparison, no cipher fitting."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean
from benchmarks import text_generation_comparison as prior
from voynich_smt.data.corpus import digest, write_json

OUT=Path('experiments/results/context-prediction')
UNK='<UNK>'
MODELS={'unigram':('unigram',50,1),'word-10':('word',10,1),'word-50':('word',50,1),
        'length-50':('length',50,1),'suffix1-50':('suffix1',50,1),'suffix2-50':('suffix2',50,1)}


def words(block): return [''.join(w) for w in block['words']]


def prepare():
    source=prior.prepare(); raw_path=Path('data/processed/zl-eva.json'); raw=json.loads(raw_path.read_text())
    held_folios={b['folio'] for b in source['heldout']}
    used={(b['folio'],b['start']) for b in source['heldout']+source['development']}
    held=[b for b in prior.blocks(raw['records']) if b['folio'] in held_folios and (b['folio'],b['start']) not in used]
    assert len(held)==10 and len({b['folio'] for b in held})==7
    p={'prior_sha256':digest(source),'source_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
       'development':source['development'],'heldout':held,'minimum_vocabulary_count':2,'unigram_pseudocount':.5,
       'base_models':MODELS,'shuffle_seeds':[23001,23002,23003],'bootstrap_seed':23004,'bootstrap_repetitions':2000,
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(prior.__file__))},
       'scope':'Same development16 blocks/12 folios, ten fresh disjoint64-word blocks on seven previously heldout folios. Previous heldout descriptive statistics were examined; these new block predictions were not. Exact fixed eligible-block enumeration, no outcome selection. Vocabulary mincount2 per training fold; singleton/unknown outcomes map to one UNK class. Past actual word may supply suffix/length, never future target. Leave-one-folio-out development selection, then freeze before fresh heldout scores. First word uses unigram; no transition across block/barrier. Log2 scores; per-folio aggregation; no plaintext/key inference.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def context(previous,model):
    kind=model['kind']
    if kind=='word': return previous if previous in model['vocabulary'] else UNK
    if kind=='length': return str(min((len(previous)-1)//2,3))
    if kind=='suffix1': return previous[-1:]
    if kind=='suffix2': return previous[-2:]
    return None


def fit(blocks,kind='unigram',alpha=50,weight=1):
    counts=Counter(w for b in blocks for w in words(b))
    vocab=sorted(w for w,n in counts.items() if n>=2)+[UNK]
    mapped=Counter({w:n for w,n in counts.items() if w in vocab}); mapped[UNK]=sum(n for w,n in counts.items() if w not in vocab)
    model={'kind':kind,'alpha':alpha,'weight':weight,'vocabulary':vocab,'unigrams':dict(mapped),'tokens':sum(mapped.values()),'pairs':{},'outgoing':{}}
    pairs=defaultdict(Counter)
    for b in blocks:
        seq=words(b)
        for a,b in zip(seq,seq[1:]): pairs[context(a,model)][b if b in vocab else UNK]+=1
    model['pairs']={str(a):dict(row) for a,row in pairs.items()}; model['outgoing']={str(a):sum(row.values()) for a,row in pairs.items()}
    return model


def probability(target,previous,model):
    target=target if target in model['vocabulary'] else UNK
    base=(model['unigrams'].get(target,0)+.5)/(model['tokens']+.5*len(model['vocabulary']))
    if previous is None or model['kind']=='unigram': return base
    ctx=str(context(previous,model)); total=model['outgoing'].get(ctx,0)
    conditional=(model['pairs'].get(ctx,{}).get(target,0)+model['alpha']*base)/(total+model['alpha'])
    return model['weight']*conditional+(1-model['weight'])*base


def score(block,model):
    seq=words(block); log=[]; known=[]
    for i,w in enumerate(seq):
        value=math.log2(probability(w,seq[i-1] if i else None,model)); log.append(value)
        if w in model['vocabulary']: known.append(value)
    return {'bits_per_token':-mean(log),'tokens':len(seq),'known_tokens':len(known),'unknown_tokens':len(seq)-len(known),
            'known_bits_per_token':-mean(known) if known else None}


def evaluate(training,evaluation,spec):
    model=fit(training,*spec); baseline=fit(training)
    rows=[]
    for block in evaluation:
        prediction=score(block,model); base=score(block,baseline)
        rows.append({'folio':block['folio'],'start':block['start'],**prediction,'baseline_bits_per_token':base['bits_per_token'],
                     'gain_bits_per_token':base['bits_per_token']-prediction['bits_per_token'],
                     'known_gain_bits_per_token':base['known_bits_per_token']-prediction['known_bits_per_token'] if prediction['known_tokens'] else None})
    return rows


def aggregate(rows):
    grouped=defaultdict(list)
    for row in rows: grouped[row['folio']].append(row)
    folios=[{'folio':folio,'gain':mean(r['gain_bits_per_token'] for r in values),
             'bits_per_token':mean(r['bits_per_token'] for r in values),
             'known_gain':mean(r['known_gain_bits_per_token'] for r in values if r['known_gain_bits_per_token'] is not None)} for folio,values in sorted(grouped.items())]
    return {'folio_mean_gain':mean(r['gain'] for r in folios),'folio_mean_bits_per_token':mean(r['bits_per_token'] for r in folios),
            'known_token_gain':sum(r['known_gain_bits_per_token']*r['known_tokens'] for r in rows if r['known_tokens'])/sum(r['known_tokens'] for r in rows),
            'unknown_tokens':sum(r['unknown_tokens'] for r in rows),'tokens':sum(r['tokens'] for r in rows),'folios':folios,'rows':rows}


def cross_validate(p,spec):
    rows=[]
    for folio in sorted({b['folio'] for b in p['development']}):
        rows+=evaluate([b for b in p['development'] if b['folio']!=folio],[b for b in p['development'] if b['folio']==folio],spec)
    return aggregate(rows)


def iteration(index):
    p=prepare(); path=OUT/f'iteration-{index}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{index-1}.json').read_text()) if index>1 else None
    names={1:[],2:['unigram'],3:['word-10','word-50'],4:['length-50','suffix1-50','suffix2-50'],5:[],6:[],7:list(MODELS)}[index]
    plan={'iteration':index,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'models':names,'holdout_access':index==7}
    write_json(OUT/f'plan-{index}.json',plan)
    if index==1:
        m=fit(p['development'],'word',10)
        for prev in (None,'daiin','notseen'):
            assert abs(sum(probability(w,prev,m) for w in m['vocabulary'])-1)<1e-10
        result={'assessment':'Probability normalization and explicit UNKNOWN class checked. Context never crosses64-word blocks. All later comparisons use log scoring on the same fold vocabulary.'}
    elif index in (2,3,4):
        evaluated={name:cross_validate(p,MODELS[name]) for name in names}
        result={'models':evaluated,'assessment':f'Development fold gains: '+str({k:round(v['folio_mean_gain'],5) for k,v in evaluated.items()})}
    elif index==5:
        prior_scores={name:row for i in (3,4) for name,row in json.loads((OUT/f'iteration-{i}.json').read_text())['models'].items()}
        best=max(prior_scores,key=lambda name:(prior_scores[name]['folio_mean_gain'],name))
        spec=MODELS[best]; mixtures={f'{best}-weight-{weight}':(spec[0],spec[1],weight) for weight in (.25,.5)}
        result={'specs':mixtures,'base_selected':best,'models':{name:cross_validate(p,spec) for name,spec in mixtures.items()},
                'assessment':'Weak-context interpolation tested at two predeclared weights using only development folios; no heldout selection.'}
    elif index==6:
        scores={name:row for i in (2,3,4,5) for name,row in json.loads((OUT/f'iteration-{i}.json').read_text())['models'].items()}
        specs={**MODELS,**json.loads((OUT/'iteration-5.json').read_text())['specs']}
        selected=max(scores,key=lambda name:(scores[name]['folio_mean_gain'],name))
        result={'selected':selected,'selected_spec':specs[selected],'development_gains':{name:row['folio_mean_gain'] for name,row in scores.items()},
                'assessment':f'Freeze {selected} for heldout evaluation; unigram remains eligible if context worsens development log scores.'}
    else:
        selection=json.loads((OUT/'iteration-6.json').read_text()); specs={**MODELS,**json.loads((OUT/'iteration-5.json').read_text())['specs']}
        evaluated={name:aggregate(evaluate(p['development'],p['heldout'],spec)) for name,spec in specs.items()}
        chosen=evaluated[selection['selected']]; shuffled=[]; model=fit(p['development'],*selection['selected_spec'])
        for block in p['heldout']:
            original=score(block,model)
            for seed in p['shuffle_seeds']:
                shuffled_words=list(block['words']); random.Random(seed+block['start']).shuffle(shuffled_words)
                permutation={**block,'words':shuffled_words}; permuted=score(permutation,model)
                shuffled.append({'folio':block['folio'],'start':block['start'],'seed':seed,'original_bits':original['bits_per_token'],'shuffled_bits':permuted['bits_per_token'],'ordering_gain':permuted['bits_per_token']-original['bits_per_token']})
        gains=[f['gain'] for f in chosen['folios']]; rng=random.Random(p['bootstrap_seed'])
        bootstrap=sorted(mean(rng.choices(gains,k=len(gains))) for _ in range(p['bootstrap_repetitions']))
        result={'selected':selection['selected'],'models':evaluated,'selected_gain_bootstrap_95':[bootstrap[50],bootstrap[1949]],
                'shuffle_diagnostic':shuffled,'assessment':'Heldout scores do not change selection. Folio bootstrap is descriptive for seven previously heldout folios; UNK-class log loss is not probability of exact novel spelling. Report known-word gain separately.'}
    report={'plan':plan,**result}; write_json(path,report); print(index,report['assessment'],flush=True); return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(args.iteration)
    else: prepare()
