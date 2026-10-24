"""Constrain repair to new candidate pairs while freezing the old emission table."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_candidate_expansion_iteration36 import OUT as FULL,FLAGS,DATA,FITS,HARD,BASELINE,EXACT,SEEDS,MAX_ITER,TOL,EPSILON,load,save,digest
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics
from voynich_smt.candidate_expansion import expand
from voynich_smt.budgeted_candidate_repair import repair_prior,anchored_emission,repair_log_prior,repair_step

OUT=FULL.parent/'iteration37'
BUDGETS=(.001,.01,.05,.1)
PRIMARY=.01


def fit_run(chain,base,obs,gold,masks,initial,prior,budget):
    repair=np.asarray(initial).copy();sums=repair.sum(axis=1,keepdims=True);repair=np.divide(repair,sums,out=np.zeros_like(repair),where=sums>0);initial=repair.copy();trace=[];converged=False
    for iteration in range(MAX_ITER+1):
        ll,gamma=forward_backward(chain,anchored_emission(base,repair,budget),obs['sequences']);lp=repair_log_prior(repair,prior)
        trace.append(dict(iteration=iteration,log_likelihood=ll,prior=lp,objective=ll+lp,scores=token_metrics(np.concatenate(gamma).argmax(axis=1),gold,masks)))
        if iteration:
            gain=trace[-1]['objective']-trace[-2]['objective'];assert gain>=-1e-6
            if gain<=TOL*max(1.,abs(trace[-2]['objective'])):converged=True;break
        if iteration==MAX_ITER:break
        repair=repair_step(chain,base,repair,obs['sequences'],prior,budget)
    return dict(trace=trace,converged=converged,initial_repair=initial.tolist(),final_repair=repair.tolist())


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for filename in (FULL/'verification-manifest.json',FITS/'verification-manifest.json',FLAGS/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);proposals=[p for p in load(FULL/'proposals.json') if p['k']==2]
    OUT.mkdir();save(OUT/'proposals.json',proposals)
    paths=[Path(__file__),Path('src/voynich_smt/budgeted_candidate_repair.py'),Path('src/voynich_smt/latent_cipher_classes.py'),FULL/'verification-manifest.json',FULL/'proposals.json',FULL/'evaluation.json',FITS/'verification-manifest.json',FLAGS/'verification-manifest.json',DATA/'observations.json',DATA/'observation-truth.json',EXACT/'support-truth.json',BASELINE/'schedules.json',HARD/'deletions.json',BASELINE.parent/'iteration28/chains.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},budgets=BUDGETS,primary_budget=PRIMARY,proposal_k=2,strategies=['context','random'],epsilon_old=EPSILON,seeds=SEEDS,max_iter=MAX_ITER,tolerance=TOL,
        scope='Same inspected background200/query40; exact frozen iteration36 K2 proposals, flags, and original model. Oracle upstream metadata retained; no fresh/reserved scoring.',
        emission='E_new(s,w)=(1-delta_s)*E_old(s,w)+delta_s*R(s,w). E_old is frozen full iteration32 mixture. R only new proposal pairs, normalized per active state; delta_s=budget for states with new pairs, zero otherwise.',
        optimization='Only repair distribution R fitted. State-specific corpus-frequency prior mass1; expected repair-channel counts in M-step; fixed budget and old emissions/chain. Five random repair starts; objective selection within same cell only.',
        controls='Fixed corpus-frequency repair R without EM; matched random K2 proposals; full global-refit iteration36 result; unchanged baseline at budget0. No query selection of budget.',
        caveat='Old table is fixed as a component, not entrywise unchanged in total mixture. Outside proposed words, class odds change by at most factors 1-budget and 1/(1-budget) from active-state rescaling, before contextual propagation.',
        evaluation='Excluded recovery, spoiled originally correct tags, accuracy, original fixed abstention, primary vs global refit and controls. Candidate inventory unchanged from iteration36; no recursive updates.'))
    save(OUT/'fit-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));index=[]
    for proposal in proposals:
        seed=proposal['mask_seed'];rate=proposal['rate'];arm=proposal['arm'];support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);newpairs=expand(support,proposal['additions'])&~support;prior=repair_prior(q,newpairs);old=load(FITS/f'fits-{seed}-{rate}-{EPSILON}-{arm}.json');base=mixture(old['random'][old['selected']]['final_component'],q,EPSILON);gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset'])
        for budget in BUDGETS:
            print('Budgeted repair',seed,rate,arm,proposal['strategy'],budget,flush=True);runs=[]
            for init_seed in SEEDS:
                initial=np.random.default_rng(init_seed).gamma(2.,1.,size=prior.shape)*prior
                runs.append(dict(seed=init_seed,**fit_run(chain,base,obs,gold,masks,initial,prior,budget)))
            selected=max(range(5),key=lambda i:runs[i]['trace'][-1]['objective']);_,gamma=forward_backward(chain,anchored_emission(base,prior,budget),obs['sequences']);fixed=token_metrics(np.concatenate(gamma).argmax(axis=1),gold,masks)
            filename=f"fits-{seed}-{rate}-{arm}-{proposal['strategy']}-{budget}.json";save(OUT/filename,dict(**{k:proposal[k] for k in ('mask_seed','rate','arm','strategy')},budget=budget,selected=selected,runs=runs,frequency_only_scores=fixed));index.append(filename)
    save(OUT/'fit-index.json',index);print('Saved',len(index),'cells /',len(index)*5,'fits',flush=True)

if __name__=='__main__':run()
