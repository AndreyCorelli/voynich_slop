"""Seven-stage line-position control for out-of-folio suffix prediction."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean
from benchmarks import context_prediction as prior
from voynich_smt.data.corpus import digest, write_json

OUT=Path('experiments/results/line-context-prediction')
UNK='<UNK>'
BASE_SPECS={'unigram':{'position':0,'gate':'none'},'position-start':{'position':2,'gate':'none'},'position-bins':{'position':4,'gate':'none'}}
SUFFIX_SPECS={f'suffix-{gate}':{'position':0,'gate':gate} for gate in ('all','within','cross')}


def annotate(block,records):
    selected=records[block['start']:block['end_exclusive']]
    assert len(selected)==64 and [r['tokens'] for r in selected]==block['words']
    assert all(r['locus'] is not None and r['word_in_locus']>=0 for r in selected)
    return {**block,'line_ids':[f"{r['folio']}:{r['locus']}:{r['physical_line']}" for r in selected],
            'positions':[r['word_in_locus'] for r in selected]}


def prepare():
    source=prior.prepare(); earlier=prior.prior.prepare(); path=Path('data/processed/zl-eva.json'); raw=json.loads(path.read_text())
    used_folios={b['folio'] for b in earlier['heldout']}
    candidates=[b for b in prior.prior.blocks(raw['records']) if int(hashlib.sha256(b['folio'].encode()).hexdigest()[:8],16)%4==0 and b['folio'] not in used_folios]
    assert len(candidates)==11 and len({b['folio'] for b in candidates})==5
    p={'prior_sha256':digest(source),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
       'development':[annotate(b,raw['records']) for b in source['development']],
       'heldout':[annotate(b,raw['records']) for b in candidates],
       'base_specs':BASE_SPECS,'suffix_specs':SUFFIX_SPECS,'strength':50,'mixture':.5,'shuffle_seeds':[24001,24002,24003],
       'code_sha256':{str(f):digest(f.read_text()) for f in (Path(__file__),Path(prior.__file__),Path(prior.prior.__file__))},
       'scope':'Same16 development blocks/12 folios; all11 eligible blocks on five entirely new folios in reserved SHA256 partition. Same clean atomic EVA and mincount2+UNK vocabulary. Layout uses transcription locus/physical line proxy and word_in_locus index, no future ending status or target glyphs. Strongly smoothed positional baseline and suffix controls, LOFO selection then fresh heldout scores. No cipher or semantic inference. Shuffles preserve exact word counts within ordinal position bins per block.'}
    p=json.loads(json.dumps(p)); out=OUT/'prepared.json'
    if out.exists(): assert json.loads(out.read_text())==p
    else: write_json(out,p)
    return p


def position_bin(index,kind):
    if kind==0: return 'all'
    if kind==2: return 'start' if index==0 else 'inside'
    if kind==4: return '0' if index==0 else '1' if index==1 else '2-3' if index<=3 else '4+'
    raise ValueError(kind)


def stratum(block,i):
    if i==0: return 'block-start'
    return 'within' if block['line_ids'][i]==block['line_ids'][i-1] else 'cross'


def active(block,i,gate): return i>0 and (gate=='all' or gate==stratum(block,i))


def fit(blocks,spec):
    counts=Counter(''.join(w) for b in blocks for w in b['words']); vocab=sorted(w for w,n in counts.items() if n>=2)+[UNK]
    uni=Counter({w:n for w,n in counts.items() if w in vocab}); uni[UNK]=sum(n for w,n in counts.items() if w not in vocab)
    positions=defaultdict(Counter); transitions=defaultdict(Counter)
    for b in blocks:
        words=[''.join(w) for w in b['words']]
        for i,w in enumerate(words):
            target=w if w in vocab else UNK; pos=position_bin(b['positions'][i],spec['position']); positions[pos][target]+=1
            if active(b,i,spec['gate']): transitions[pos+'|'+words[i-1][-1]][target]+=1
    return {'spec':spec,'vocabulary':vocab,'unigrams':dict(uni),'tokens':sum(uni.values()),
            'positions':{k:dict(v) for k,v in positions.items()},'transitions':{k:dict(v) for k,v in transitions.items()}}


def probability(block,i,model):
    w=''.join(block['words'][i]); target=w if w in model['vocabulary'] else UNK
    base=(model['unigrams'].get(target,0)+.5)/(model['tokens']+.5*len(model['vocabulary']))
    pos=position_bin(block['positions'][i],model['spec']['position'])
    if model['spec']['position']:
        counts=model['positions'].get(pos,{})
        conditional=(counts.get(target,0)+50*base)/(sum(counts.values())+50)
        base=.5*base+.5*conditional
    if active(block,i,model['spec']['gate']):
        ctx=pos+'|'+''.join(block['words'][i-1])[-1]; counts=model['transitions'].get(ctx,{})
        conditional=(counts.get(target,0)+50*base)/(sum(counts.values())+50)
        base=.5*base+.5*conditional
    return base


def evaluate(train,blocks,spec):
    model=fit(train,spec); unigram=fit(train,BASE_SPECS['unigram']); position=fit(train,{'position':spec['position'],'gate':'none'})
    rows=[]
    for b in blocks:
        tokens=[]
        for i,w in enumerate(b['words']):
            loss=-math.log2(probability(b,i,model)); uniloss=-math.log2(probability(b,i,unigram)); posloss=-math.log2(probability(b,i,position))
            tokens.append({'stratum':stratum(b,i),'known':''.join(w) in model['vocabulary'],'loss':loss,'gain_unigram':uniloss-loss,'gain_position':posloss-loss})
        rows.append({'folio':b['folio'],'start':b['start'],'tokens':tokens})
    return rows


def aggregate(rows):
    grouped=defaultdict(list)
    for row in rows: grouped[row['folio']]+=row['tokens']
    folios=[]
    for folio,tokens in sorted(grouped.items()):
        folios.append({'folio':folio,'gain_unigram':mean(t['gain_unigram'] for t in tokens),'gain_position':mean(t['gain_position'] for t in tokens),
            'loss':mean(t['loss'] for t in tokens),'strata':{s:{'tokens':sum(t['stratum']==s for t in tokens),
                'gain_position':mean(t['gain_position'] for t in tokens if t['stratum']==s)} for s in ('within','cross','block-start') if any(t['stratum']==s for t in tokens)}})
    all_tokens=[t for row in rows for t in row['tokens']]; known=[t for t in all_tokens if t['known']]
    return {'gain_unigram':mean(f['gain_unigram'] for f in folios),'gain_position':mean(f['gain_position'] for f in folios),
            'loss':mean(f['loss'] for f in folios),'known_gain_position':mean(t['gain_position'] for t in known) if known else None,
            'unknown_tokens':len(all_tokens)-len(known),'tokens':len(all_tokens),'folios':folios,'rows':rows}


def cv(p,spec):
    rows=[]
    for folio in sorted({b['folio'] for b in p['development']}):
        rows+=evaluate([b for b in p['development'] if b['folio']!=folio],[b for b in p['development'] if b['folio']==folio],spec)
    return aggregate(rows)


def permutation(block,seed):
    result={**block,'words':list(block['words'])}; groups=defaultdict(list); rng=random.Random(seed+block['start'])
    for i,pos in enumerate(block['positions']): groups[position_bin(pos,4)].append(i)
    for indices in groups.values():
        words=[block['words'][i] for i in indices]; rng.shuffle(words)
        for i,w in zip(indices,words): result['words'][i]=w
    return result


def iteration(index):
    p=prepare(); out=OUT/f'iteration-{index}.json'
    if out.exists(): return json.loads(out.read_text())
    previous=json.loads((OUT/f'iteration-{index-1}.json').read_text()) if index>1 else None
    specs={}
    if index==2: specs=BASE_SPECS
    elif index==3: specs=SUFFIX_SPECS
    elif index==4:
        baseline=json.loads((OUT/'iteration-2.json').read_text())['selected_position']
        pos=BASE_SPECS[baseline]['position']; specs={f'position+suffix-{gate}':{'position':pos,'gate':gate} for gate in ('all','within','cross')}
    plan={'iteration':index,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'specs':specs,'holdout_access':index==7}
    write_json(OUT/f'plan-{index}.json',plan)
    if index==1:
        counts=Counter(stratum(b,i) for b in p['development'] for i in range(64))
        result={'development_strata':dict(counts),'assessment':'Line proxy, ordinal bins and development strata frozen. Word identity is not used to define target position.'}
    elif index in (2,3,4):
        scores={name:cv(p,spec) for name,spec in specs.items()}; result={'models':scores}
        if index==2: result['selected_position']=max(('position-start','position-bins'),key=lambda name:(scores[name]['gain_unigram'],name))
        result['assessment']='Development gains over unigram: '+str({name:round(r['gain_unigram'],5) for name,r in scores.items()})
    elif index==5:
        four=json.loads((OUT/'iteration-4.json').read_text()); best=max(four['models'],key=lambda name:(four['models'][name]['gain_position'],name))
        spec=four['plan']['specs'][best]; diagnostic=[]
        for folio in sorted({b['folio'] for b in p['development']}):
            train=[b for b in p['development'] if b['folio']!=folio]
            for b in [b for b in p['development'] if b['folio']==folio]:
                original=evaluate(train,[b],spec)[0]
                for seed in p['shuffle_seeds']:
                    shuffled=evaluate(train,[permutation(b,seed)],spec)[0]
                    diagnostic.append({'folio':folio,'start':b['start'],'seed':seed,'ordering_gain':mean(t['loss'] for t in shuffled['tokens'])-mean(t['loss'] for t in original['tokens'])})
        result={'context_candidate':best,'diagnostic':diagnostic,'mean_ordering_gain':mean(r['ordering_gain'] for r in diagnostic),'assessment':'Position-bin-preserving permutation tests development order dependence; model selection remains based on unpermuted LOFO scores.'}
    elif index==6:
        collected={name:row for stage in (2,3,4) for name,row in json.loads((OUT/f'iteration-{stage}.json').read_text())['models'].items()}
        all_specs={name:spec for stage in (2,3,4) for name,spec in json.loads((OUT/f'iteration-{stage}.json').read_text())['plan']['specs'].items()}
        selected=max(collected,key=lambda name:(collected[name]['gain_unigram'],name))
        controlled=[name for name in all_specs if name.startswith('position+suffix')]
        selected_context=max(controlled,key=lambda name:(collected[name]['gain_position'],name))
        result={'selected':selected,'controlled_context':selected_context,'specs':all_specs,'development_scores':{name:{k:r[k] for k in ('gain_unigram','gain_position')} for name,r in collected.items()},
                'assessment':f'Freeze overall {selected} and position-controlled diagnostic {selected_context}, without heldout ranking.'}
    else:
        selection=json.loads((OUT/'iteration-6.json').read_text()); specs=selection['specs']
        scores={name:aggregate(evaluate(p['development'],p['heldout'],spec)) for name,spec in specs.items()}; diagnostic=[]
        spec=specs[selection['controlled_context']]
        for b in p['heldout']:
            original=evaluate(p['development'],[b],spec)[0]
            for seed in p['shuffle_seeds']:
                shuffled=evaluate(p['development'],[permutation(b,seed)],spec)[0]
                diagnostic.append({'folio':b['folio'],'start':b['start'],'seed':seed,'ordering_gain':mean(t['loss'] for t in shuffled['tokens'])-mean(t['loss'] for t in original['tokens'])})
        result={'selected':selection['selected'],'controlled_context':selection['controlled_context'],'models':scores,'diagnostic':diagnostic,
                'assessment':'Fresh heldout scores leave selections fixed. Compare within/cross strata and gain over matching position baseline; do not equate predictive order with language or a copying mechanism.'}
    report={'plan':plan,**result}; write_json(out,report); print(index,result['assessment'],flush=True); return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(args.iteration)
    else: prepare()
