"""Seven frozen calibration stages for the prior spelling predictor; no model tuning."""
import argparse
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
import random
from statistics import mean
import string
from benchmarks import character_prediction as pred
from benchmarks.character_prediction_validation import manual
from voynich_smt.data.corpus import digest, write_json

OUT=Path('experiments/results/character-calibration')
SEEDS=(26001,26002)


def latin_blocks(template,words,offset):
    blocks=copy.deepcopy(template); cursor=offset
    for b in blocks:
        n=len(b['words']); b['words']=[list(w) for w in words[cursor:cursor+n]]; b['latin_start']=cursor; cursor+=n
        assert len(b['words'])==n
    return blocks


def transform(blocks,kind,seed):
    rng=random.Random(seed); out=copy.deepcopy(blocks)
    alphabet=list(string.ascii_lowercase); permutation=alphabet[:]; rng.shuffle(permutation); mono=dict(zip(alphabet,permutation))
    pairs=[a+b for a in alphabet for b in alphabet]; rng.shuffle(pairs); code={a:[pairs[2*i],pairs[2*i+1]] for i,a in enumerate(alphabet)}
    for b in out:
        if kind=='shuffle': b.update(pred.prior.permutation(b,seed)); continue
        for i,w in enumerate(b['words']):
            if kind=='mono': b['words'][i]=[mono[c] for c in w]
            elif kind in ('expand','homophonic'): b['words'][i]=list(''.join(code[c][0 if kind=='expand' else rng.randrange(2)] for c in w))
            elif kind=='positive' and i>0 and b['line_ids'][i]==b['line_ids'][i-1]: b['words'][i][0]=b['words'][i-1][-1]
    return out


def prepare():
    prior=pred.prepare(); frozen=json.loads((pred.OUT/'iteration-6.json').read_text()); spec=frozen['specs'][frozen['selected']]
    path=Path('data/processed/caesar-latin-v2.json'); raw=json.loads(path.read_text()); words=[''.join(r['tokens']).replace('v','u') for r in raw['records'] if r['excluded_reason'] is None and r['tokens']]
    assert all(set(w)<=set(string.ascii_lowercase) for w in words)
    cases={}; intervals=[]
    for seed in SEEDS:
        # Nonoverlapping contiguous prose samples. Fixed random starting offset within each half.
        begin=random.Random(seed).randrange(0,500)+(0 if seed==SEEDS[0] else len(words)//2)
        train=latin_blocks(prior['development'],words,begin); held=latin_blocks(prior['heldout'],words,begin+1024)
        intervals.append([begin,begin+3872]); cases[f'latin-{seed}']={'train':train,'heldout':held,'seed':seed,'kind':'plain'}
        for kind in ('mono','expand','homophonic'):
            cases[f'{kind}-{seed}']={'train':transform(train,kind,seed),'heldout':transform(held,kind,seed),'seed':seed,'kind':kind}
        cases[f'latin-shuffle-{seed}']={'train':transform(train,'shuffle',seed),'heldout':transform(held,'shuffle',seed),'seed':seed,'kind':'shuffle'}
    assert intervals[0][1]<=intervals[1][0] and intervals[1][1]<=len(words)
    for kind in ('shuffle','positive'):
        cases[f'eva-{kind}']={'train':transform(prior['development'],kind,SEEDS[0]),'heldout':transform(prior['heldout'],kind,SEEDS[0]),'kind':kind,'seed':SEEDS[0]}
    p={'prior_sha256':digest(prior),'selection_sha256':digest(frozen),'spec':spec,'latin_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'latin_intervals':intervals,'cases':cases,
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(pred.__file__),Path('benchmarks/character_prediction_validation.py'))},
       'stages':{'1':['latin-26001'],'2':['mono-26001'],'3':['expand-26001'],'4':['homophonic-26001'],'5':['latin-shuffle-26001','eva-shuffle'],'6':['eva-positive'],'7':['latin-26002','mono-26002','expand-26002','homophonic-26002','latin-shuffle-26002']},
       'scope':'Frozen prior second-order/position/suffix model, no selection. Latin j-to-i from cached parser, v-to-u here. Same 1024 training /2848 held words and manuscript layout slots, no claim of historical Latin lines. Distinct contiguous Latin seed samples, matched cases share words/layout. Mono permutes all26 labels. Expansion gives each letter one unique two-character code; homophonic chooses uniformly among two unique two-character codes independently. Shared key across train/test, no vocabulary restriction. Positional word permutation performed separately in each block for train/test. Positive control sets within-line initial letter to preceding output final letter. Alphabet stays26; length unchanged except expansion doubles it. EOS scored. Characters are encoded labels, not manuscript glyphs. Per-word and per-character gains reported. Prior manuscript scores reused, no fresh manuscript replication. No likelihood ratio among historical mechanisms.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def summarize(result):
    groups=defaultdict(list)
    for row in result['rows']: groups[row['folio']]+=row['tokens']
    return {'bits_per_character':result['bits_per_character'],'gain_position_per_character':result['gain_position'],
            'gain_position_per_word':mean(sum(t['gain_position'] for t in ts)/len(ts) for ts in groups.values()),
            'positive_folios':sum(f['gain_position']>0 for f in result['folios']),'folios':len(result['folios']),
            'mean_word_length':result['characters']/result['words'],'novel_words':result['novel_words'],'words':result['words'],
            'novel_gain_position_per_character':result['novel_gain_position']}


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'cases':p['stages'][str(i)],'model_selection':False}
    write_json(OUT/f'plan-{i}.json',plan); results={}
    for name in plan['cases']:
        case=p['cases'][name]; results[name]=pred.aggregate(pred.evaluate(case['train'],case['heldout'],p['spec']))
    assessments={1:'Plain prose reference scored; next test label invariance.',2:'Bijective relabeling should preserve scores exactly; next separate expansion from random homophones.',3:'Deterministic expansion reference scored; next random homophonic choice.',4:'Random homophonic encoding scored; next assess order-free surrogates.',5:'Refitted position-preserving surrogates scored; next confirm detection on an explicit boundary dependence.',6:'Positive boundary control scored; next replicate all Latin transformations on a disjoint prose sample.',7:'Independent prose sample completes calibration; compare the frozen statistic without mechanism ranking.'}
    report={'plan':plan,'results':results,'summary':{name:summarize(r) for name,r in results.items()},'assessment':assessments[i]}
    write_json(path,report); print(i,report['assessment'],json.dumps(report['summary']),flush=True); return report


def validate():
    p=prepare(); scores=0; reports=[]
    for i in range(1,8):
        r=json.loads((OUT/f'iteration-{i}.json').read_text()); assert r['plan']==json.loads((OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None); reports.append(r)
        for name,result in r['results'].items():
            case=p['cases'][name]
            for row,b in zip(result['rows'],case['heldout'],strict=True):
                for spec,gain in ((p['spec'],None),({**p['spec'],'gate':'none'},'gain_position'),({**p['spec'],'position':0,'gate':'none'},'gain_noexternal'),(pred.BASE_SPECS['char-iid'],'gain_iid')):
                    expected=manual(case['train'],b,spec)
                    for t,(loss,novel) in zip(row['tokens'],expected,strict=True):
                        assert abs((t['loss'] if gain is None else t['loss']+t[gain])-loss)<1e-10
                        assert t['novel']==novel; scores+=1
            assert pred.aggregate(result['rows'])==result and summarize(result)==r['summary'][name]
    for seed in SEEDS:
        plain=next(r['results'][f'latin-{seed}'] for r in reports if f'latin-{seed}' in r['results']); mono=next(r['results'][f'mono-{seed}'] for r in reports if f'mono-{seed}' in r['results'])
        for a,b in zip(plain['rows'],mono['rows'],strict=True):
            for x,y in zip(a['tokens'],b['tokens'],strict=True): assert abs(x['loss']-y['loss'])<1e-10 and abs(x['gain_position']-y['gain_position'])<1e-10
    for name,case in p['cases'].items():
        if case['kind'] not in ('mono','expand','homophonic','shuffle'): continue
        original=p['cases'][f"latin-{case['seed']}"] if not name.startswith('eva-') else {'train':pred.prepare()['development'],'heldout':pred.prepare()['heldout']}
        for split in ('train','heldout'):
            for a,b in zip(original[split],case[split],strict=True):
                assert a['positions']==b['positions'] and a['line_ids']==b['line_ids']
                if case['kind']=='shuffle':
                    for bin in ('0','1','2-3','4+'):
                        av=sorted(''.join(w) for w,n in zip(a['words'],a['positions']) if pred.prior.position_bin(n,4)==bin); bv=sorted(''.join(w) for w,n in zip(b['words'],b['positions']) if pred.prior.position_bin(n,4)==bin); assert av==bv
                else: assert [len(w)*(2 if case['kind'] in ('expand','homophonic') else 1) for w in a['words']]==list(map(len,b['words']))
    write_json(OUT/'validation.json',{'stages':7,'independent_event_word_scores':scores,'bijective_score_invariance':True,'matched_lengths_layout_and_shuffle_multisets':True,'status':'passed'}); print('Validated',scores,'independent word/model scores',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--iteration',type=int,choices=range(1,8)); parser.add_argument('--run',action='store_true'); parser.add_argument('--validate',action='store_true'); args=parser.parse_args()
    if args.validate: validate()
    elif args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(args.iteration)
    else: prepare()
