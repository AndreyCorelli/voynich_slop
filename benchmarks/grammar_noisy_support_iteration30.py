"""False-positive candidate stress test on existing development only."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_supported_classes_iteration29 import OUT as EXACT,BASELINE,PREVIOUS,SEEDS,MAX_ITER,TOL,load,save,digest
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_step,supported_log_prior
from voynich_smt.noisy_class_support import support_schedule,noisy_support,subset_score

OUT=EXACT.parent/'iteration30'
RATES=(.01,.05,.10,.25,.50,1.)
MASK_SEEDS=(3001,3002,3003,3004,3005)


def metrics(gamma,truth,obs,reference,affected):
    query=obs['offset'];v=reference.shape[1];out={}
    for name,mask in [('all',np.ones(v,bool)),('affected',affected),('originally_ambiguous',reference.sum(axis=0)>1),('affected_singletons',affected&(reference.sum(axis=0)==1))]:
        out[name]=subset_score(gamma,truth,obs['sequences'],mask)
        out[name+'_query']=subset_score(gamma[query:],truth[query:],obs['sequences'][query:],mask)
    return out


def fit_run(chain,obs,truth,reference,affected,initial,prior,sharing):
    e=np.array(initial);e/=e.sum(axis=1,keepdims=True);trace=[];first_net_loss=None;converged=False;initial=e.copy()
    for iteration in range(MAX_ITER+1):
        ll,gamma=forward_backward(chain,e,obs['sequences']);lp=supported_log_prior(e,prior,sharing);m=metrics(gamma,truth,obs,reference,affected)
        row=dict(iteration=iteration,log_likelihood=ll,prior=lp,objective=ll+lp,**m);trace.append(row)
        if iteration:
            gain=row['objective']-trace[-2]['objective'];assert gain>=-1e-6
            if first_net_loss is None and gain>1e-8 and m['all']['correct']<trace[-2]['all']['correct']:first_net_loss=iteration
            if gain<=TOL*max(1.,abs(trace[-2]['objective'])):converged=True;break
        if iteration==MAX_ITER:break
        e=supported_step(chain,e,obs['sequences'],prior,sharing)
    return dict(trace=trace,initial_emissions=initial.tolist(),final_emissions=e.tolist(),converged=converged,first_net_loss=first_net_loss)


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for filename in (EXACT/'verification-manifest.json',BASELINE/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    st=load(EXACT/'support-truth.json');reference=np.asarray(st['support']);counts=np.asarray(st['gold_counts']);obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chain=load(BASELINE/'chains.json')['oracle_development'];schedules={str(seed):support_schedule(reference,seed) for seed in MASK_SEEDS}
    OUT.mkdir();save(OUT/'schedules.json',schedules)
    paths=[Path(__file__),Path('src/voynich_smt/noisy_class_support.py'),Path('src/voynich_smt/supported_emissions.py'),EXACT/'verification-manifest.json',EXACT/'support-truth.json',EXACT/'results.json',BASELINE/'chains.json',BASELINE/'verification-manifest.json',PREVIOUS/'observations.json',PREVIOUS/'observation-truth.json',PREVIOUS/'verification-manifest.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},schedules_hash=digest(OUT/'schedules.json'),rates=RATES,mask_seeds=MASK_SEEDS,initialization_seeds=SEEDS,max_iter=MAX_ITER,tolerance=TOL,
        scope='Existing calibration40/background200 only; reference support and chain oracle; no target/reserved scoring.',
        perturbation='Nested random ordering of word types per seed. Add exactly one uniformly sampled reference-forbidden class to first floor(rate*V) types. All gold support retained. Rate1 is one extra class/type, not unrestricted8.',
        priors='Same support-conditioned priors as iteration29, recomputed per mask. Oracle and five random initializations per arm/mask/rate. Base rate0 reused from iteration29.',
        selection='Maximum regularized objective among five random starts per mask/arm/rate; oracle start separate privileged diagnostic. Never compare objective across masks/arms.',
        baselines='Uniform-within-candidates expected accuracy and candidate-only argmax oracle corpus class frequency; same support, no word-count EM.',
        evaluation='Full/query, affected types, affected originally-singleton types, and originally ambiguous types; summaries across five mask seeds are perturbation spread, not population confidence intervals.'))
    q,_,_=prior_data(obs['sequences'],obs['word_endings']);index=[]
    for seed in MASK_SEEDS:
        for rate in RATES:
            support,affected=noisy_support(reference,schedules[str(seed)],rate);prior=supported_prior(obs['sequences'],obs['word_endings'],support)
            for arm in ('word','ending'):
                sharing=arm=='ending';print('Mask',seed,'rate',rate,arm,flush=True);initial=supported_update(counts,prior,sharing)
                oracle=fit_run(chain,obs,truth,reference,affected,initial,prior,sharing);random=[]
                for init_seed in SEEDS:
                    e=np.random.default_rng(init_seed).gamma(2.,1.,size=counts.shape)*q[None,:]*support
                    random.append(dict(seed=init_seed,**fit_run(chain,obs,truth,reference,affected,e,prior,sharing)))
                selected=max(range(len(random)),key=lambda i:random[i]['trace'][-1]['objective']);filename=f'fits-{seed}-{rate}-{arm}.json'
                save(OUT/filename,dict(mask_seed=seed,rate=rate,arm=arm,selected=selected,oracle=oracle,random=random));index.append(filename)
    save(OUT/'fit-index.json',index);print('Saved',len(index),'cells,',len(index)*6,'fits',flush=True)

if __name__=='__main__':run()
