"""Challenge fixed-transition likelihood on already inspected development only."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_latent_classes_iteration26 import OUT as PREVIOUS,SEEDS,load,save,digest
from benchmarks.grammar_latent_classes_iteration26_evaluate import class_metrics
from voynich_smt.latent_cipher_classes import oracle_emissions,forward_backward,prior_data,log_prior
from voynich_smt.oracle_emission_challenge import em_step,snapshot,changed_tokens

OUT=PREVIOUS.parent/'iteration27'
MAX_ITER=600
TOL=1e-7


def score(gamma,truth):
    y=np.concatenate(truth);p=np.concatenate(gamma).argmax(axis=1);labels=np.unique(y)
    return dict(tokens=len(y),correct=int((p==y).sum()),accuracy=float((p==y).mean()),balanced_accuracy=float(np.mean([(p[y==s]==s).mean() for s in labels])))


def audit(chain,before,after,obs,truth,sharing):
    seq=obs['sequences'];we=obs['word_endings'];a=snapshot(chain,before,seq,we,sharing);b=snapshot(chain,after,seq,we,sharing)
    _,ga=forward_backward(chain,before,seq);_,gb=forward_backward(chain,after,seq)
    counts=np.zeros_like(before)
    for s,g in zip(seq,ga):
        for w,p in zip(s,g):counts[:,w]+=p
    q_delta=float(np.sum(counts*np.log(after/before)))
    # Fixed chain: Q(new|old)-Q(old|old) contains only emission change.
    return dict(before=a,after=b,delta={k:b[k]-a[k] for k in a},old_posterior_expected_emission_delta=q_delta,
        posterior_kl_old_to_new=b['log_likelihood']-a['log_likelihood']-q_delta,
        changes=changed_tokens(ga,gb,truth,seq,obs['offset']),before_emissions=before.tolist(),after_emissions=after.tolist())


def trajectory(chain,obs,truth,initial,sharing,inspect=False):
    e=np.asarray(initial).copy();e/=e.sum(axis=1,keepdims=True);q,qe,within=prior_data(obs['sequences'],obs['word_endings']);trace=[];first_loss=None;first_net_loss=None;initial_e=e.copy();converged=False
    for iteration in range(MAX_ITER+1):
        ll,gamma=forward_backward(chain,e,obs['sequences']);prior=log_prior(e,obs['word_endings'],q,qe,within,sharing)
        row=dict(iteration=iteration,log_likelihood=ll,prior=prior,objective=ll+prior,all=score(gamma,truth),query=score(gamma[obs['offset']:],truth[obs['offset']:]))
        trace.append(row)
        if iteration:
            gain=row['objective']-trace[-2]['objective'];assert gain>=-1e-6
            changes=changed_tokens(previous_gamma,gamma,truth,obs['sequences'],obs['offset']) if inspect else []
            if inspect and first_loss is None and gain>1e-8 and any(c['lost'] for c in changes):
                first_loss=dict(iteration=iteration,**audit(chain,previous_e,e,obs,truth,sharing))
            if inspect and first_net_loss is None and gain>1e-8 and row['all']['correct']<trace[-2]['all']['correct']:
                first_net_loss=dict(iteration=iteration,before=trace[-2],after=row)
            if gain<=TOL*max(1.,abs(trace[-2]['objective'])):converged=True;break
        if iteration==MAX_ITER:break
        previous_e=e.copy();previous_gamma=gamma;e=em_step(chain,e,obs['sequences'],obs['word_endings'],sharing)
    return dict(trace=trace,converged=converged,initial_emissions=initial_e.tolist(),final_emissions=e.tolist(),first_corruption=first_loss,first_net_accuracy_loss=first_net_loss,
        final_class_metrics=class_metrics(gamma[obs['offset']:],truth[obs['offset']:]))


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    oldmanifest=load(PREVIOUS/'verification-manifest.json')
    for p,h in oldmanifest['inputs'].items():assert digest(p)==h,p
    inputs=[Path(__file__),Path('src/voynich_smt/oracle_emission_challenge.py'),PREVIOUS/'verification-manifest.json',PREVIOUS/'source-models.json',PREVIOUS/'observations.json',PREVIOUS/'observation-truth.json']
    OUT.mkdir();save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in inputs},scope='Development calibration40+background200 from iteration26 only; no fresh scoring or reserve access',
        max_iter=MAX_ITER,tolerance=TOL,seeds=SEEDS,arms=['word','ending'],initialization='Same smoothed supervised emissions as iteration26 oracle, separately under each arm prior; five original random initializations',
        first_corruption='First strictly improving update that changes any previously correct token to wrong; also record first net all-corpus accuracy loss',
        selection='No new parameter/threshold selection; labels used only in oracle initialization and diagnostics',
        components='Posterior expected start/transition/stop/emission log probabilities, posterior entropy, emission regularizer; independent log-space decomposition'))
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chain=load(PREVIOUS/'source-models.json')['chains']['pooled'];results={}
    for arm in ('word','ending'):
        sharing=arm=='ending';initial=oracle_emissions(chain,obs['sequences'],obs['word_endings'],truth,sharing)
        print('Oracle',arm,flush=True);oracle=trajectory(chain,obs,truth,initial,sharing,True);random=[]
        q,_,_=prior_data(obs['sequences'],obs['word_endings'])
        for seed in SEEDS:
            print('Random',arm,seed,flush=True);e=np.random.default_rng(seed).gamma(2.,1.,size=initial.shape)*q[None,:]
            random.append(dict(seed=seed,**trajectory(chain,obs,truth,e,sharing)))
        results[arm]=dict(oracle=oracle,random=random)
        r=oracle['trace'];print(arm,'oracle initial/final',r[0]['query'],r[-1]['query'],'gain',r[-1]['objective']-r[0]['objective'],'converged',oracle['converged'],'first_corruption',oracle['first_corruption']['iteration'] if oracle['first_corruption'] else None,flush=True)
    save(OUT/'results.json',results)

if __name__=='__main__':run()
