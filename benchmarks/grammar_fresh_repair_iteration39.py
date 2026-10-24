"""Fresh confirmation of frozen iteration38 repair policies; label-free fitting."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_latent_classes_iteration26 import ROOT,TREEBANK,RESERVE,load,save,strings,observe,digest,SEEDS
from benchmarks.scalable_latin_caesar import words,PROIEL
from voynich_smt.class_alignment import tag_class
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.supported_emissions import supported_prior,supported_log_prior
from voynich_smt.fallback_emissions import mixture,mixture_step
from voynich_smt.noisy_class_support import support_schedule
from voynich_smt.missing_class_support import deletion_schedule,missing_support
from voynich_smt.masked_class_context import masked_context
from voynich_smt.candidate_abstention import flag
from voynich_smt.candidate_expansion import propose,expand
from voynich_smt.budgeted_candidate_repair import repair_prior,anchored_emission,repair_log_prior,repair_step
from voynich_smt.repair_budget_selection import edit_counts
OUT=ROOT/'iteration39'

def fit(initial,emission,penalty,step,sequences,chain):
    value=initial.copy();s=value.sum(axis=1,keepdims=True);value=np.divide(value,s,out=np.zeros_like(value),where=s>0);trace=[]
    for i in range(601):
        ll,_=forward_backward(chain,emission(value),sequences);objective=ll+penalty(value);trace.append(objective)
        if i:
            assert objective>=trace[-2]-1e-6
            if objective-trace[-2]<=1e-7*max(1,abs(trace[-2])):break
        if i<600:value=step(value)
    return dict(component=value.tolist(),trace=trace,converged=i<600)

def prepare():
    assert not OUT.exists()
    for p,h in load(ROOT/'iteration38/verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    files=sorted(set(ROOT.rglob('*manifest*.json'))|set(ROOT.rglob('*truth*.json')))
    used=set().union(*(set(strings(load(p))) for p in files));reserved={r['sent_id'] for g in load(RESERVE)['authors'].values() for r in g};data={'Jerome':[],'Caesar':[]}
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None);source=next((l.split(' = ',1)[1].split(',')[0] for l in lines if l.startswith('# source = ')),None);author=PROIEL.get(source)
        if sid in reserved or sid in used or author not in data or len(data[author])>=100:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')]
        if any('-' in r[0] for r in rows):continue
        kept=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];norm=[words(r[1]) for r in kept]
        if not 3<=len(kept)<=60 or any(len(w)!=1 for w in norm):continue
        data[author].append(dict(sent_id=sid,tokens=[w[0] for w in norm],classes=[tag_class(r[3],'fine') for r in kept]))
    assert all(len(v)==100 for v in data.values()),{k:len(v) for k,v in data.items()}
    OUT.mkdir();obs={};truth={};references={}
    for author,rows in data.items():
        assert observe(rows)==observe(rows,26032)
        obs[author]=dict(observe(rows),offset=60,query_ids=[r['sent_id'] for r in rows[60:]])
        truth[author]=[r['classes'] for r in rows];ref=np.zeros((8,len(obs[author]['word_endings'])),bool)
        for seq,gold in zip(obs[author]['sequences'],truth[author]):ref[gold,seq]=True
        references[author]=ref.tolist()
    save(OUT/'observations.json',obs);save(OUT/'observation-truth.json',truth);save(OUT/'support-truth.json',references)
    save(OUT/'configuration.json',dict(chain=load(ROOT/'iteration28/chains.json')['oracle_development'],flags={a:load(ROOT/'iteration35/policies.json')[f'{a}/0.01/outside_mass/0.01'] for a in ('word','ending')},budgets={f'{a}/{s}':load(ROOT/'iteration38/policies.json')[f'{a}/{s}/0.01']['budget'] for a in ('word','ending') for s in ('context','random')}))
    inputs=[Path(__file__),TREEBANK,RESERVE,ROOT/'iteration28/chains.json',ROOT/'iteration35/policies.json',ROOT/'iteration38/policies.json',ROOT/'iteration38/verification-manifest.json']+list(Path('src/voynich_smt').glob('*.py'))
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in inputs},prior_declarations={str(p):digest(p) for p in files},split_ids={a:[r['sent_id'] for r in rows] for a,rows in data.items()},background=60,queries=40,seeds=SEEDS,mask_seeds=list(range(3001,3006)),rates=[.1,.5],epsilon=.01,max_iter=600,tolerance=1e-7,scope='Fresh controlled mechanism confirmation; oracle corpus support and previously frozen oracle development chain. Anonymous word/ending inputs, supplied boundaries, transductive adaptation. No fresh policy calibration or chain estimation; reserve skipped before annotation parsing.'))
    save(OUT/'fit-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))

def run():
    prepare();config=load(OUT/'configuration.json');chain=config['chain'];proposals=[];bases={}
    for author,obs in load(OUT/'observations.json').items():
        seq=obs['sequences'];q,_,_=prior_data(seq,obs['word_endings']);ref=np.array(load(OUT/'support-truth.json')[author])
        for seed in range(3001,3006):
            for rate in (.1,.5):
                support,_=missing_support(ref,support_schedule(ref,seed),deletion_schedule(ref,seed+100),rate);prior=supported_prior(seq,obs['word_endings'],support)
                for arm in ('word','ending'):
                    key=f'{author}-{seed}-{rate}-{arm}';sharing=arm=='ending';runs=[]
                    for initseed in SEEDS:
                        initial=np.random.default_rng(initseed).gamma(2.,1.,size=support.shape)*prior['word']
                        runs.append(fit(initial,lambda a:mixture(a,q,.01),lambda a:supported_log_prior(a,prior,sharing),lambda a:mixture_step(chain,a,seq,prior,q,.01,sharing),seq,chain))
                    selected=max(range(5),key=lambda i:runs[i]['trace'][-1]);base=mixture(runs[selected]['component'],q,.01);bases[key]=base
                    save(OUT/f'baseline-{key}.json',dict(selected=selected,runs=runs))
                    context=np.concatenate([masked_context(chain,base[:,s].T)['posterior'] for s in seq]);wordids=np.concatenate(seq);outside=np.sum(context*(~support[:,wordids]).T,axis=1);flagged=flag(outside,config['flags'][arm])
                    for strategy in ('context','random'):
                        additions=propose(support,wordids,context,flagged,k=2,strategy=strategy,seed=36000+seed)
                        proposals.append(dict(key=key,author=author,seed=seed,rate=rate,arm=arm,strategy=strategy,additions=additions,flagged=flagged.tolist(),budget=config['budgets'][f'{arm}/{strategy}']))
                    print('Baseline',key,flush=True)
    save(OUT/'proposals.json',proposals);save(OUT/'repair-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));predictions=[]
    for p in proposals:
        obs=load(OUT/'observations.json')[p['author']];seq=obs['sequences'];q,_,_=prior_data(seq,obs['word_endings']);ref=np.array(load(OUT/'support-truth.json')[p['author']]);support,_=missing_support(ref,support_schedule(ref,p['seed']),deletion_schedule(ref,p['seed']+100),p['rate']);prior=repair_prior(q,expand(support,p['additions'])&~support);base=bases[p['key']];budget=p['budget'];runs=[]
        for seed in SEEDS:
            initial=np.random.default_rng(seed).gamma(2.,1.,size=prior.shape)*prior
            runs.append(fit(initial,lambda r:anchored_emission(base,r,budget),lambda r:repair_log_prior(r,prior),lambda r:repair_step(chain,base,r,seq,prior,budget),seq,chain))
        selected=max(range(5),key=lambda i:runs[i]['trace'][-1]);emission=anchored_emission(base,runs[selected]['component'],budget)
        decode=lambda e:np.concatenate(forward_backward(chain,e,seq)[1]).argmax(axis=1).tolist()
        predictions.append(dict(**p,baseline=decode(base),prediction=decode(emission)))
        save(OUT/f"repair-{p['key']}-{p['strategy']}.json",dict(selected=selected,runs=runs));print('Repair',p['key'],p['strategy'],flush=True)
    save(OUT/'predictions.json',predictions);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))

def evaluate():
    for p,h in load(OUT/'evaluation-freeze.json')['inputs'].items():assert digest(p)==h,p
    obs=load(OUT/'observations.json');truth=load(OUT/'observation-truth.json');groups={}
    for row in load(OUT/'predictions.json'):
        start=sum(map(len,obs[row['author']]['sequences'][:60]));gold=np.concatenate(truth[row['author']])[start:];counts=edit_counts(row['baseline'][start:],row['prediction'][start:],gold)
        key=f"{row['author']}/{row['rate']}/{row['arm']}/{row['strategy']}";groups.setdefault(key,[]).append(counts)
    result={}
    for key,rows in groups.items():
        totals={k:sum(r[k] for r in rows) for k in rows[0]};totals.update(baseline_accuracy=totals['baseline_correct']/totals['tokens'],accuracy=(totals['baseline_correct']+totals['net'])/totals['tokens'],spoil_rate=totals['spoiled']/totals['baseline_correct'],gain=totals['net']/totals['tokens']);result[key]=totals
    save(OUT/'evaluation.json',result)
    print(result)

if __name__=='__main__':run();evaluate()
