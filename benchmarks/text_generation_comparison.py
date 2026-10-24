"""Seven-stage offline comparison of copying/templates with natural-text controls."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean, median, pstdev
from benchmarks.manuscript_width_audit import clean
from voynich_smt.data.corpus import digest, write_json

OUT=Path('experiments/results/text-generation-comparison')
SIZE=64
SEEDS=(21001,21002,21003)
METRICS=('mean_length','unique_ratio','adjacent_repeat','repeat_local_excess','one_edit_pair_fraction','one_edit_local_excess')
STAGES={1:'Validate measurement invariants',2:'Frequency baselines and natural controls',3:'Copying without mutation',4:'Copying with mutation',5:'Independent and locally persistent templates',6:'Freeze development-selected generator',7:'Evaluate all frozen models on heldout folios'}
MODELS=('char-iid','word-iid','natural-h1','natural-h2','copy-20','copy-50','copy-80','mutate-20','mutate-50','mutate-80','template-iid','template-local')


def one_edit(a,b):
    if a==b or abs(len(a)-len(b))>1: return False
    if len(a)==len(b): return sum(x!=y for x,y in zip(a,b))==1
    if len(a)>len(b): a,b=b,a
    i=j=0; skipped=False
    while i<len(a):
        if a[i]==b[j]: i+=1; j+=1
        elif skipped: return False
        else: skipped=True; j+=1
    return True


def metrics(words):
    n=len(words)
    if n<2: raise ValueError('At least two words required')
    pairs=[(i,j) for i in range(n) for j in range(i+1,n)]
    local=[(i,j) for i,j in pairs if j-i<=8]
    exact=lambda pairs:sum(words[i]==words[j] for i,j in pairs)/len(pairs)
    near=lambda pairs:sum(one_edit(words[i],words[j]) for i,j in pairs)/len(pairs)
    return {'mean_length':mean(map(len,words)),'unique_ratio':len(set(words))/n,
        'adjacent_repeat':sum(a==b for a,b in zip(words,words[1:]))/(n-1),
        'repeat_local_excess':exact(local)-exact(pairs),
        'one_edit_pair_fraction':near(pairs),'one_edit_local_excess':near(local)-near(pairs)}


def blocks(records,manuscript=True):
    result=[]; pending=[]; folio=None
    for index,r in enumerate(records):
        if manuscript and r.get('folio')!=folio: pending=[]; folio=r.get('folio')
        eligible=clean(r) if manuscript else bool(r['tokens']) and r.get('excluded_reason') is None
        if not eligible: pending=[]; continue
        word=tuple(r['tokens'])
        if not manuscript: word=tuple(''.join(word).replace('j','i').replace('v','u'))
        pending.append((index,word))
        if len(pending)==SIZE:
            result.append({'folio':folio,'start':pending[0][0],'end_exclusive':index+1,'words':[list(w) for _,w in pending]}); pending=[]
    return result


def prepare():
    raw_paths=[Path('data/processed/zl-eva.json'),Path('data/processed/caesar-latin-v2.json')]
    raw=[json.loads(p.read_text()) for p in raw_paths]
    candidates=blocks(raw[0]['records']); dev=[]; held=[]
    for b in candidates:
        bucket=int(hashlib.sha256(b['folio'].encode()).hexdigest()[:8],16)%4
        (held if bucket==0 else dev).append(b)
    rng=random.Random(20001); rng.shuffle(dev); rng.shuffle(held)
    assert len(dev)>=16 and len(held)>=12
    dev=dev[:16]; held=held[:12]
    natural=blocks(raw[1]['records'],False); random.Random(20002).shuffle(natural); natural=natural[:16]
    p={'size':SIZE,'seeds':SEEDS,'development':dev,'heldout':held,'natural_controls':natural,'metrics':METRICS,
       'source_sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in raw_paths},
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path('benchmarks/manuscript_width_audit.py'))},
       'scope':'64-word nonoverlapping clean blocks; exclude barriers and folio crossings. SHA256 folio bucket0 heldout, others development. Fixed shuffled sampling16 development/12 heldout blocks, 16 Caesar controls. All generator training uses development only. Three fixed seeds. Copying/template models are descriptive competitors, not historical mechanisms. Natural H1 permutation preserves plaintext word structure; H2 uses independent two opaque homophone labels per letter to isolate splitting, not a glyph-alphabet/width-feasible manuscript encoder. No keys fitted, no Z3, no language probability.'}
    # JSON canonicalization handles tuples consistently before comparison.
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def training(p):
    words=[tuple(w) for b in p['development'] for w in b['words']]
    chars=Counter(c for w in words for c in w)
    return {'words':words,'chars':sorted(chars),'weights':[chars[c] for c in sorted(chars)],
        'prefixes':[w[:1] for w in words if len(w)>=3], 'stems':[w[1:-1] for w in words if len(w)>=3],
        'suffixes':[w[-1:] for w in words if len(w)>=3]}


def generate(model,t,natural,seed):
    rng=random.Random(seed); pool=t['words']; output=[]
    if model=='natural-h1': return list(natural) # metrics invariant under injective glyph permutation
    if model=='natural-h2':
        return [tuple(f'{c}:{rng.randrange(2)}' for c in word) for word in natural]
    for i in range(SIZE):
        if model=='char-iid':
            length=len(rng.choice(pool)); word=tuple(rng.choices(t['chars'],weights=t['weights'],k=length))
        elif model=='word-iid': word=rng.choice(pool)
        elif model.startswith(('copy-','mutate-')):
            probability=int(model.split('-')[1])/100
            if output and rng.random()<probability:
                word=rng.choice(output[-8:])
                if model.startswith('mutate-') and rng.random()<.25:
                    position=rng.randrange(len(word)); choices=[c for c in t['chars'] if c!=word[position]]
                    word=word[:position]+(rng.choice(choices),)+word[position+1:]
            else: word=rng.choice(pool)
        elif model.startswith('template-'):
            if model=='template-local' and i and rng.random()<.5: stem=last_stem
            else: stem=rng.choice(t['stems'])
            word=rng.choice(t['prefixes'])+stem+rng.choice(t['suffixes']); last_stem=stem
        else: raise ValueError(model)
        output.append(word)
    return output


def normalization(p):
    measured=[metrics([tuple(w) for w in b['words']]) for b in p['development']]
    return {k:{'center':mean(r[k] for r in measured),'scale':max(pstdev(r[k] for r in measured),.01)} for k in METRICS}


def evaluate(p,models,held=False):
    target=p['heldout'] if held else p['development']; t=training(p); norm=normalization(p)
    target_metrics=[metrics([tuple(w) for w in b['words']]) for b in target]
    results={}
    for model in models:
        rows=[]
        for i,b in enumerate(target):
            natural=[tuple(w) for w in p['natural_controls'][i]['words']]
            for seed in SEEDS:
                generated=generate(model,t,natural,seed+1000*i)
                m=metrics(generated)
                deviations={k:abs(m[k]-target_metrics[i][k])/norm[k]['scale'] for k in METRICS}
                rows.append({'block':i,'seed':seed,'metrics':m,'target_metrics':target_metrics[i],
                             'normalized_absolute_deviation':deviations,'distance':mean(deviations.values()),
                             'structural_distance':mean(v for k,v in deviations.items() if k!='mean_length')})
        results[model]={'mean_distance':mean(r['distance'] for r in rows),'median_distance':median(r['distance'] for r in rows),
                        'mean_structural_distance':mean(r['structural_distance'] for r in rows),'rows':rows}
    return results


def iteration(index):
    p=prepare(); path=OUT/f'iteration-{index}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{index-1}.json').read_text()) if index>1 else None
    plan={'iteration':index,'objective':STAGES[index],'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,
          'models':{1:[],2:list(MODELS[:4]),3:list(MODELS[4:7]),4:list(MODELS[7:10]),5:list(MODELS[10:]),6:[],7:list(MODELS)}[index],
          'holdout_access':index==7}
    write_json(OUT/f'plan-{index}.json',plan)
    if index==1:
        examples=[('a',),('a',),('b',),('a','b')]*16
        shuffled=list(examples); random.Random(3).shuffle(shuffled)
        a,b=metrics(examples),metrics(shuffled)
        for k in ('mean_length','unique_ratio','one_edit_pair_fraction'): assert a[k]==b[k]
        assert generate('word-iid',training(p),[],1)==generate('word-iid',training(p),[],1)
        result={'checks_passed':True,'assessment':'Global word/family metrics are order-invariant; local excess metrics isolate ordering against each block global pair baseline. These measurements are descriptive, not a likelihood.'}
    elif index in (2,3,4,5):
        results=evaluate(p,plan['models']); best=min(results,key=lambda m:results[m]['mean_distance'])
        result={'models':results,'assessment':f'Best development distance in this stage: {best}. Next family is tested with fixed parameters; no new grid values chosen after scores.'}
    elif index==6:
        scores={name:row for i in range(2,6) for name,row in json.loads((OUT/f'iteration-{i}.json').read_text())['models'].items()}
        generators=[m for m in MODELS if not m.startswith('natural-')]
        selected=min(generators,key=lambda m:(scores[m]['mean_distance'],m))
        structure=min(generators,key=lambda m:(scores[m]['mean_structural_distance'],m))
        result={'selected_generator':selected,'structural_only_selected':structure,'development_scores':{m:{k:scores[m][k] for k in ('mean_distance','mean_structural_distance')} for m in MODELS},
                'assessment':'Freeze the all-metric selection before reading heldout statistics. Structural-only ranking is a predefined sensitivity, not a replacement selection. No p-values or historical causation claims.'}
    else:
        selected=json.loads((OUT/'iteration-6.json').read_text())['selected_generator']; results=evaluate(p,plan['models'],True)
        result={'selected_generator':selected,'models':results,'assessment':f'Heldout evaluated once for all frozen models; {selected} remains the development selection regardless of heldout winner. Blocks/seeds are descriptive repeats, not independent trials.'}
    report={'plan':plan,**result}; write_json(path,report)
    print(index,STAGES[index],report['assessment'],flush=True)
    return report


def run():
    for index in range(1,8): iteration(index)
    p=prepare(); results=json.loads((OUT/'iteration-7.json').read_text())
    summary={name:{k:r[k] for k in ('mean_distance','mean_structural_distance')} for name,r in results['models'].items()}
    write_json(OUT/'summary.json',{'selected_generator':results['selected_generator'],'heldout_scores':summary,'scope':p['scope']})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run: run()
    elif args.iteration: iteration(args.iteration)
    else: prepare()
