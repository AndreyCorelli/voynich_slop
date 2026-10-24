"""Fixed-mass emission fallback for missing candidates on inspected development."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_missing_support_iteration31 import OUT as HARD,BASELINE,EXACT,PREVIOUS,SEEDS,MASK_SEEDS,MAX_ITER,TOL,load,save,digest
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_log_prior
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics
from voynich_smt.fallback_emissions import mixture,mixture_step,fallback_posteriors

OUT=HARD.parent/'iteration32'
RATES=(0.,.1,.5)
EPSILONS=(.001,.01,.1,.3)
PRIMARY=.01


def fit_run(chain,obs,gold,masks,initial,prior,frequency,epsilon,sharing):
    component=np.asarray(initial).copy();component/=component.sum(axis=1,keepdims=True);initial=component.copy();trace=[];converged=False
    for iteration in range(MAX_ITER+1):
        emission=mixture(component,frequency,epsilon);ll,gamma=forward_backward(chain,emission,obs['sequences']);lp=supported_log_prior(component,prior,sharing)
        score=token_metrics(np.concatenate(gamma).argmax(axis=1),gold,masks);trace.append(dict(iteration=iteration,log_likelihood=ll,prior=lp,objective=ll+lp,scores=score))
        if iteration:
            gain=trace[-1]['objective']-trace[-2]['objective'];assert gain>=-1e-6
            if gain<=TOL*max(1.,abs(trace[-2]['objective'])):converged=True;break
        if iteration==MAX_ITER:break
        component=mixture_step(chain,component,obs['sequences'],prior,frequency,epsilon,sharing)
    fallback=fallback_posteriors(component,frequency,epsilon,obs['sequences'],gamma)
    return dict(trace=trace,converged=converged,initial_component=initial.tolist(),final_component=component.tolist(),
        fallback_use={name:float(fallback[mask].mean()) if mask.any() else None for name,mask in masks.items()})


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for filename in (HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    reference=np.asarray(load(EXACT/'support-truth.json')['support']);counts=np.asarray(load(EXACT/'support-truth.json')['gold_counts']);obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings'])
    OUT.mkdir();paths=[Path(__file__),Path('src/voynich_smt/fallback_emissions.py'),Path('src/voynich_smt/supported_emissions.py'),Path('src/voynich_smt/latent_cipher_classes.py'),HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json',HARD/'deletions.json',BASELINE/'schedules.json',EXACT/'support-truth.json',PREVIOUS/'observations.json',PREVIOUS/'observation-truth.json',BASELINE.parent/'iteration28/chains.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},rates=RATES,epsilons=EPSILONS,primary_epsilon=PRIMARY,mask_seeds=MASK_SEEDS,initialization_seeds=SEEDS,max_iter=MAX_ITER,tolerance=TOL,
        scope='Previously inspected calibration40/background200; no fresh/reserved scoring. Oracle chain/candidate metadata remain privileged.',
        emission='p(w|s)=(1-epsilon)*candidate_component(w|s)+epsilon*q(w), q fixed corpus word frequency shared by every state. Component has hard support; full emission does not.',
        objective='Observed mixture HMM likelihood plus unchanged supported prior on component. E-step also estimates mixture-channel responsibilities; M-step counts only candidate-channel responsibility. epsilon fixed, not fitted.',
        selection='epsilon=.01 primary fixed before scoring; others sensitivity only. Five random starts selected by within-cell regularized objective; separate surviving-label oracle start. No cross-epsilon objective selection.',
        controls='Rate0 matched hard baseline from iteration30 rate1; rate.1/.5 hard masks/fits from iteration31. Component starts match these hard arms exactly; no labels enter EM or selection.',
        evaluation='Recovery of excluded classes, losses/gains on identical covered tokens, total errors and fallback posterior use. Fallback use is not abstention or a calibrated error detector.'))
    index=[]
    for seed in MASK_SEEDS:
        for rate in RATES:
            support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);prior=supported_prior(obs['sequences'],obs['word_endings'],support);gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset'])
            for epsilon in EPSILONS:
                for arm in ('word','ending'):
                    sharing=arm=='ending';print('Fallback',seed,rate,epsilon,arm,flush=True);initial=supported_update(counts*support,prior,sharing)
                    oracle=fit_run(chain,obs,gold,masks,initial,prior,q,epsilon,sharing);random=[]
                    for init_seed in SEEDS:
                        component=np.random.default_rng(init_seed).gamma(2.,1.,size=counts.shape)*q[None,:]*support
                        random.append(dict(seed=init_seed,**fit_run(chain,obs,gold,masks,component,prior,q,epsilon,sharing)))
                    selected=max(range(5),key=lambda i:random[i]['trace'][-1]['objective']);filename=f'fits-{seed}-{rate}-{epsilon}-{arm}.json'
                    save(OUT/filename,dict(mask_seed=seed,rate=rate,epsilon=epsilon,arm=arm,selected=selected,oracle=oracle,random=random));index.append(filename)
    save(OUT/'fit-index.json',index);print('Saved',len(index),'cells /',len(index)*6,'fits',flush=True)

if __name__=='__main__':run()
