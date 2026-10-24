"""Seven-stage open-vocabulary EVA spelling prediction with layout controls."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean
import string
from benchmarks import line_context_prediction as prior
from benchmarks.manuscript_width_audit import clean
from voynich_smt.data.corpus import digest, write_json

OUT=Path('experiments/results/character-prediction')
BOS='<BOS>'; EOS='<EOS>'
BASE_SPECS={'char-iid':{'order':0,'strength':10,'position':0,'gate':'none'},
            'char-1-10':{'order':1,'strength':10,'position':0,'gate':'none'},
            'char-2-10':{'order':2,'strength':10,'position':0,'gate':'none'},
            'char-2-50':{'order':2,'strength':50,'position':0,'gate':'none'}}


def prepare():
    source=prior.prepare(); original=prior.prior.prior.prepare(); word_context=prior.prior.prepare()
    raw_path=Path('data/processed/zl-eva.json'); raw=json.loads(raw_path.read_text()); used=set()
    for b in original['development']+original['heldout']+word_context['heldout']+source['heldout']:
        used.update(range(b['start'],b['end_exclusive']))
    dev=[]
    for b in source['development']:
        for offset in (0,32):
            dev.append({**b,'start':b['start']+offset,'end_exclusive':b['start']+offset+32,
                'words':b['words'][offset:offset+32],'positions':b['positions'][offset:offset+32],'line_ids':b['line_ids'][offset:offset+32]})
    held=[]; pending=[]; folio=None
    for i,r in enumerate(raw['records']):
        if r['folio']!=folio: pending=[]; folio=r['folio']
        if i in used or not clean(r) or int(hashlib.sha256(folio.encode()).hexdigest()[:8],16)%4!=0:
            pending=[]; continue
        pending.append((i,r))
        if len(pending)==32:
            held.append({'folio':folio,'start':pending[0][0],'end_exclusive':i+1,
                'words':[r['tokens'] for _,r in pending],'positions':[r['word_in_locus'] for _,r in pending],
                'line_ids':[f"{r['folio']}:{r['locus']}:{r['physical_line']}" for _,r in pending]}); pending=[]
    assert len(held)==89 and len({b['folio'] for b in held})==50
    p={'prior_sha256':digest(source),'source_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),'development':dev,'heldout':held,
       'base_specs':BASE_SPECS,'alphabet':list(string.ascii_lowercase),'unigram_pseudocount':.5,'external_context_strength':50,'external_context_weight':.5,
       'shuffle_seeds':[25001,25002,25003],
       'previously_evaluated_folios':sorted({b['folio'] for b in original['heldout']+word_context['heldout']+source['heldout']}),
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(prior.__file__),Path('benchmarks/manuscript_width_audit.py'))},
       'scope':'Same1024 development words on12 folios split into32-word blocks. All89 fresh nonoverlapping32-word blocks on50 reserved folios after excluding every earlier training/evaluation token. Some folios were previously evaluated on other words; shorter extraction changes cohort. Open spelling over26 lowercase letters plus EOS, no word UNK or evaluation lexicon. Nonempty-word BOS excludes EOS. LOFO development selection, freeze then heldout; full-word probabilities scored in bits/character including end-event cost. Position and preceding suffix affect first glyph only. No cipher/semantic inference.'}
    p=json.loads(json.dumps(p)); out=OUT/'prepared.json'
    if out.exists(): assert json.loads(out.read_text())==p
    else: write_json(out,p)
    return p


def key(parts): return '|'.join(parts)


def fit(blocks,spec):
    uni=Counter(); gram1=defaultdict(Counter); gram2=defaultdict(Counter); positions=defaultdict(Counter); suffixes=defaultdict(Counter)
    spellings=set()
    for b in blocks:
        for i,letters in enumerate(b['words']):
            spellings.add(''.join(letters)); history=[BOS,BOS]
            for glyph in list(letters)+[EOS]:
                uni[glyph]+=1; gram1[history[-1]][glyph]+=1; gram2[key(history[-2:])][glyph]+=1; history.append(glyph)
            pos=prior.position_bin(b['positions'][i],spec['position']); positions[pos][letters[0]]+=1
            if prior.active(b,i,spec['gate']): suffixes[pos+'|'+b['words'][i-1][-1]][letters[0]]+=1
    return {'spec':spec,'unigram':dict(uni),'gram1':{k:dict(v) for k,v in gram1.items()},'gram2':{k:dict(v) for k,v in gram2.items()},
            'positions':{k:dict(v) for k,v in positions.items()},'suffixes':{k:dict(v) for k,v in suffixes.items()},'training_spellings':sorted(spellings)}


def probability(glyph,history,model,block=None,index=None):
    start=history[-1]==BOS; allowed=list(string.ascii_lowercase)+([] if start else [EOS])
    if glyph not in allowed: return 0.0
    uni=model['unigram']; base=(uni.get(glyph,0)+.5)/(sum(uni.get(g,0) for g in allowed)+.5*len(allowed))
    strength=model['spec']['strength']
    for level in range(1,model['spec']['order']+1):
        counts=model['gram1'].get(history[-1],{}) if level==1 else model['gram2'].get(key(history[-2:]),{})
        base=(counts.get(glyph,0)+strength*base)/(sum(counts.get(g,0) for g in allowed)+strength)
    if start and block is not None:
        pos=prior.position_bin(block['positions'][index],model['spec']['position'])
        if model['spec']['position']:
            counts=model['positions'].get(pos,{}); conditional=(counts.get(glyph,0)+50*base)/(sum(counts.values())+50); base=(base+conditional)/2
        if prior.active(block,index,model['spec']['gate']):
            counts=model['suffixes'].get(pos+'|'+block['words'][index-1][-1],{})
            conditional=(counts.get(glyph,0)+50*base)/(sum(counts.values())+50); base=(base+conditional)/2
    return base


def score(block,model):
    rows=[]
    for i,letters in enumerate(block['words']):
        history=[BOS,BOS]; loss=0
        for glyph in list(letters)+[EOS]:
            loss-=math.log2(probability(glyph,history,model,block,i)); history.append(glyph)
        rows.append({'characters':len(letters),'loss':loss,'novel':''.join(letters) not in model['training_spellings'],'stratum':prior.stratum(block,i)})
    return rows


def evaluate(train,evaluation,spec):
    model=fit(train,spec); unigram=fit(train,BASE_SPECS['char-iid']); noexternal=fit(train,{**spec,'position':0,'gate':'none'}); position=fit(train,{**spec,'gate':'none'})
    result=[]
    for b in evaluation:
        rows=score(b,model); base=score(b,unigram); within=score(b,noexternal); pos=score(b,position)
        for i,row in enumerate(rows):
            row.update(gain_iid=base[i]['loss']-row['loss'],gain_noexternal=within[i]['loss']-row['loss'],gain_position=pos[i]['loss']-row['loss'])
        result.append({'folio':b['folio'],'start':b['start'],'tokens':rows})
    return result


def aggregate(rows):
    grouped=defaultdict(list)
    for r in rows: grouped[r['folio']]+=r['tokens']
    folios=[]
    for folio,tokens in sorted(grouped.items()):
        total=sum(t['characters'] for t in tokens)
        folios.append({'folio':folio,'characters':total,'words':len(tokens),'bits_per_character':sum(t['loss'] for t in tokens)/total,
                       **{k:sum(t[k] for t in tokens)/total for k in ('gain_iid','gain_noexternal','gain_position')}})
    tokens=[t for r in rows for t in r['tokens']]; novel=[t for t in tokens if t['novel']]
    return {'bits_per_character':mean(f['bits_per_character'] for f in folios),
            **{k:mean(f[k] for f in folios) for k in ('gain_iid','gain_noexternal','gain_position')},
            'novel_words':len(novel),'words':len(tokens),'characters':sum(t['characters'] for t in tokens),
            'novel_bits_per_character':sum(t['loss'] for t in novel)/sum(t['characters'] for t in novel) if novel else None,
            'novel_gain_position':sum(t['gain_position'] for t in novel)/sum(t['characters'] for t in novel) if novel else None,
            'folios':folios,'rows':rows}


def cv(p,spec):
    rows=[]
    for folio in sorted({b['folio'] for b in p['development']}):
        rows+=evaluate([b for b in p['development'] if b['folio']!=folio],[b for b in p['development'] if b['folio']==folio],spec)
    return aggregate(rows)


def letter_shuffle(b,seed):
    rng=random.Random(seed+b['start']); words=[]
    for w in b['words']:
        letters=list(w); rng.shuffle(letters); words.append(letters)
    return {**b,'words':words}


def iteration(index):
    p=prepare(); out=OUT/f'iteration-{index}.json'
    if out.exists(): return json.loads(out.read_text())
    previous=json.loads((OUT/f'iteration-{index-1}.json').read_text()) if index>1 else None
    specs={}
    if index==2: specs=BASE_SPECS
    elif index==4:
        selected=json.loads((OUT/'iteration-2.json').read_text())['selected_base']; base=BASE_SPECS[selected]
        specs={'base':base,'position-start':{**base,'position':2},'position-bins':{**base,'position':4}}
    elif index==5:
        four=json.loads((OUT/'iteration-4.json').read_text()); pos=four['selected_position']; base=four['plan']['specs'][pos]
        specs={f'position+suffix-{gate}':{**base,'gate':gate} for gate in ('all','within','cross')}
    plan={'iteration':index,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'specs':specs,'holdout_access':index==7}
    write_json(OUT/f'plan-{index}.json',plan)
    if index==1:
        model=fit(p['development'],BASE_SPECS['char-2-10']); b=p['development'][0]
        for history in ([BOS,BOS],[BOS,'a'],['q','o']):
            allowed=list(string.ascii_lowercase)+([] if history[-1]==BOS else [EOS])
            assert abs(sum(probability(c,history,model,b,1) for c in allowed)-1)<1e-10
        result={'assessment':'Nonempty spelling probabilities normalize, EOS has positive interior probability, every lowercase unseen glyph/spelling is scoreable without word UNK.'}
    elif index in (2,4,5):
        models={name:cv(p,spec) for name,spec in specs.items()}
        result={'models':models,'assessment':'Development bits/character: '+str({k:round(r['bits_per_character'],5) for k,r in models.items()})}
        best=min(models,key=lambda n:(models[n]['bits_per_character'],n))
        if index==2: result['selected_base']=best
        if index==4: result['selected_position']=best
    elif index==3:
        two=json.loads((OUT/'iteration-2.json').read_text()); selected=two['selected_base']; spec=BASE_SPECS[selected]; rows=[]
        for folio in sorted({b['folio'] for b in p['development']}):
            train=[b for b in p['development'] if b['folio']!=folio]; model=fit(train,spec); iid=fit(train,BASE_SPECS['char-iid'])
            for b in [b for b in p['development'] if b['folio']==folio]:
                original=sum(r['loss'] for r in score(b,model)); originaliid=sum(r['loss'] for r in score(b,iid))
                for seed in p['shuffle_seeds']:
                    shuffled=letter_shuffle(b,seed); shuffledloss=sum(r['loss'] for r in score(shuffled,model)); shufflediid=sum(r['loss'] for r in score(shuffled,iid))
                    assert abs(originaliid-shufflediid)<1e-10
                    rows.append({'folio':folio,'start':b['start'],'seed':seed,'word_order_gain_bits':shuffledloss-original})
        result={'base':selected,'diagnostic':rows,'assessment':'Character-order sensitivity checked with length/letter-multiset-preserving within-word permutations. IID spelling score is invariant. No language or cipher conclusion.'}
    elif index==6:
        collected={f'{stage}:{name}':r for stage in (2,4,5) for name,r in json.loads((OUT/f'iteration-{stage}.json').read_text())['models'].items()}
        specs={f'{stage}:{name}':spec for stage in (2,4,5) for name,spec in json.loads((OUT/f'iteration-{stage}.json').read_text())['plan']['specs'].items()}
        selected=min(collected,key=lambda n:(collected[n]['bits_per_character'],n))
        controlled=min([n for n in collected if n.startswith('5:')],key=lambda n:(-collected[n]['gain_position'],n))
        result={'selected':selected,'controlled_context':controlled,'specs':specs,
                'development_scores':{n:{k:r[k] for k in ('bits_per_character','gain_position','novel_gain_position')} for n,r in collected.items()},
                'assessment':f'Freeze overall {selected} and incremental-context diagnostic {controlled} before new cohort evaluation; no heldout model reselection.'}
    else:
        six=json.loads((OUT/'iteration-6.json').read_text()); models={name:aggregate(evaluate(p['development'],p['heldout'],spec)) for name,spec in six['specs'].items()}
        spec=six['specs'][six['controlled_context']]; model=fit(p['development'],spec); posmodel=fit(p['development'],{**spec,'gate':'none'}); diagnostic=[]
        for b in p['heldout']:
            original=sum(r['loss'] for r in score(b,model)); originalpos=sum(r['loss'] for r in score(b,posmodel))
            for seed in p['shuffle_seeds']:
                shuffled=prior.permutation(b,seed); permuted=sum(r['loss'] for r in score(shuffled,model)); permutedpos=sum(r['loss'] for r in score(shuffled,posmodel))
                assert abs(originalpos-permutedpos)<1e-10
                diagnostic.append({'folio':b['folio'],'start':b['start'],'seed':seed,'ordering_gain_bits':permuted-original,'characters':sum(map(len,b['words']))})
        result={'selected':six['selected'],'controlled_context':six['controlled_context'],'models':models,'diagnostic':diagnostic,
                'assessment':'Full spellings now scored on fresh text, including novel words. Selections unchanged. Report character grammar separately from incremental previous-word context; proper predictive probabilities are not decryption or mechanism evidence.'}
    report={'plan':plan,**result}; write_json(out,report); print(index,result['assessment'],flush=True); return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(args.iteration)
    else: prepare()
