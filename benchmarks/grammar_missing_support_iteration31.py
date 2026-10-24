"""Missing true candidates: direct coverage loss versus covered-token spillover."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_noisy_support_iteration30 import OUT as BASELINE,EXACT,PREVIOUS,SEEDS,MASK_SEEDS,RATES,MAX_ITER,TOL,load,save,digest
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_step,supported_log_prior
from voynich_smt.missing_class_support import deletion_schedule,missing_support,cohorts,token_metrics

OUT=BASELINE.parent/'iteration31'


def fit_run(chain,obs,gold,masks,initial,prior,sharing):
    e=np.asarray(initial).copy();e/=e.sum(axis=1,keepdims=True);initial=e.copy();trace=[];converged=False
    for iteration in range(MAX_ITER+1):
        ll,gamma=forward_backward(chain,e,obs['sequences']);lp=supported_log_prior(e,prior,sharing)
        score=token_metrics(np.concatenate(gamma).argmax(axis=1),gold,masks)
        trace.append(dict(iteration=iteration,log_likelihood=ll,prior=lp,objective=ll+lp,scores=score))
        if iteration:
            gain=trace[-1]['objective']-trace[-2]['objective'];assert gain>=-1e-6
            if gain<=TOL*max(1.,abs(trace[-2]['objective'])):converged=True;break
        if iteration==MAX_ITER:break
        e=supported_step(chain,e,obs['sequences'],prior,sharing)
    return dict(trace=trace,converged=converged,initial_emissions=initial.tolist(),final_emissions=e.tolist())


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for path in (BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    reference=np.array(load(EXACT/'support-truth.json')['support']);counts=np.array(load(EXACT/'support-truth.json')['gold_counts']);obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions={str(s):deletion_schedule(reference,s+100) for s in MASK_SEEDS}
    OUT.mkdir();save(OUT/'deletions.json',deletions)
    paths=[Path(__file__),Path('src/voynich_smt/missing_class_support.py'),Path('src/voynich_smt/supported_emissions.py'),Path('src/voynich_smt/latent_cipher_classes.py'),BASELINE/'verification-manifest.json',BASELINE/'schedules.json',EXACT/'support-truth.json',EXACT/'verification-manifest.json',PREVIOUS/'observations.json',PREVIOUS/'observation-truth.json',PREVIOUS/'verification-manifest.json',BASELINE.parent/'iteration28/chains.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},deletions_hash=digest(OUT/'deletions.json'),rates=RATES,mask_seeds=MASK_SEEDS,initialization_seeds=SEEDS,max_iter=MAX_ITER,tolerance=TOL,
        scope='Already inspected calibration40/background200; no new target/reserve scoring. Oracle development chain and reference candidate support remain privileged.',
        baseline='Iteration30 rate1 masks: every word has one false candidate in addition to reference support. Matched per perturbation seed/arm; reuse original selected-random baseline fits.',
        deletion='Uniformly pick one reference-supported class per type using independent seed(maskseed+100). Delete it for first floor(rate*V) words in original addition order. Nested within seed; false fallback retained, no empty inventory.',
        initialization='Five matched gamma random starts masked and normalized; separate oracle surviving-label counts (excluded gold counts removed), with unchanged support-conditioned prior strengths.',
        selection='Highest regularized objective among five random starts within cell only. Labels used for oracle masks/start and evaluation, not EM or selection.',
        metrics='Exact token coverage ceiling, covered/excluded, untouched types, covered affected types, covered adjacent-to-excluded tokens, and originally-ambiguous covered tokens; matched baseline on identical cohorts.'))
    q,_,_=prior_data(obs['sequences'],obs['word_endings']);index=[]
    for seed in MASK_SEEDS:
        for rate in RATES:
            support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);prior=supported_prior(obs['sequences'],obs['word_endings'],support);gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset'])
            for arm in ('word','ending'):
                sharing=arm=='ending';print('Deletion',seed,rate,arm,flush=True);initial=supported_update(counts*support,prior,sharing)
                oracle=fit_run(chain,obs,gold,masks,initial,prior,sharing);random=[]
                for init_seed in SEEDS:
                    e=np.random.default_rng(init_seed).gamma(2.,1.,size=counts.shape)*q[None,:]*support
                    random.append(dict(seed=init_seed,**fit_run(chain,obs,gold,masks,e,prior,sharing)))
                selected=max(range(len(random)),key=lambda i:random[i]['trace'][-1]['objective']);filename=f'fits-{seed}-{rate}-{arm}.json';save(OUT/filename,dict(mask_seed=seed,rate=rate,arm=arm,selected=selected,oracle=oracle,random=random));index.append(filename)
    save(OUT/'fit-index.json',index);print('Saved',len(index),'cells /',len(index)*6,'fits',flush=True)

if __name__=='__main__':run()
