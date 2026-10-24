"""Oracle word-class support control on existing development material."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_oracle_chain_iteration28 import OUT as BASELINE,PREVIOUS,SEEDS,MAX_ITER,TOL,load,save,digest
from benchmarks.grammar_oracle_emission_challenge_iteration27 import score
from voynich_smt.latent_cipher_classes import forward_backward,word_counts,prior_data
from voynich_smt.oracle_emission_challenge import changed_tokens
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_step,supported_log_prior

OUT=BASELINE.parent/'iteration29'


def scores(gamma,truth,sequences,support,offset):
    out=dict(all=score(gamma,truth),query=score(gamma[offset:],truth[offset:]));ambiguous=support.sum(axis=0)>1
    for name,start in [('ambiguous_all',0),('ambiguous_query',offset)]:
        y=[];p=[]
        for seq,g,t in zip(sequences[start:],gamma[start:],truth[start:]):
            mask=ambiguous[seq];y.extend(np.asarray(t)[mask]);p.extend(g.argmax(axis=1)[mask])
        y=np.asarray(y);p=np.asarray(p);classes=np.unique(y)
        out[name]=dict(tokens=len(y),correct=int((p==y).sum()),accuracy=float((p==y).mean()) if len(y) else None,
            balanced_accuracy=float(np.mean([(p[y==s]==s).mean() for s in classes])) if len(y) else None,classes=classes.tolist())
    return out


def trajectory(chain,obs,truth,initial,prior,sharing,inspect=False):
    seq=obs['sequences'];support=prior['support'];e=np.asarray(initial).copy();e/=e.sum(axis=1,keepdims=True);trace=[];first=None;converged=False;initial=e.copy()
    for iteration in range(MAX_ITER+1):
        assert not np.any(e[~support]);ll,g=forward_backward(chain,e,seq);lp=supported_log_prior(e,prior,sharing)
        row=dict(iteration=iteration,log_likelihood=ll,prior=lp,objective=ll+lp,**scores(g,truth,seq,support,obs['offset']));trace.append(row)
        if iteration:
            gain=row['objective']-trace[-2]['objective'];assert gain>=-1e-6
            if inspect and first is None and gain>1e-8:
                changes=changed_tokens(old_gamma,g,truth,seq,obs['offset'])
                if any(c['lost'] for c in changes):first=dict(iteration=iteration,changes=changes,before=trace[-2],after=row,before_emissions=old_e.tolist(),after_emissions=e.tolist())
            if gain<=TOL*max(1.,abs(trace[-2]['objective'])):converged=True;break
        if iteration==MAX_ITER:break
        old_e=e.copy();old_gamma=g;e=supported_step(chain,e,seq,prior,sharing)
    return dict(trace=trace,converged=converged,initial_emissions=initial.tolist(),final_emissions=e.tolist(),first_corruption=first)


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for manifest in (PREVIOUS/'verification-manifest.json',BASELINE/'verification-manifest.json'):
        for p,h in load(manifest)['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chain=load(BASELINE/'chains.json')['oracle_development']
    counts=word_counts(obs['sequences'],[np.eye(8)[y] for y in truth],len(obs['word_endings']),8);support=counts>0
    prior=supported_prior(obs['sequences'],obs['word_endings'],support)
    inputs=[Path(__file__),Path('src/voynich_smt/supported_emissions.py'),Path('src/voynich_smt/latent_cipher_classes.py'),BASELINE/'verification-manifest.json',BASELINE/'chains.json',BASELINE/'results.json',PREVIOUS/'observations.json',PREVIOUS/'observation-truth.json',PREVIOUS/'verification-manifest.json']
    OUT.mkdir();save(OUT/'support-truth.json',dict(support=support.tolist(),gold_counts=counts.tolist()))
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in inputs},support_hash=digest(OUT/'support-truth.json'),max_iter=MAX_ITER,tolerance=TOL,seeds=SEEDS,
        scope='Previously inspected calibration40/background200 only; exact corpus-wide observed POS support is privileged; no fresh scoring or reserve access.',
        change='Emission probabilities outside oracle-observed word/class support fixed to exact zero. Source is iteration28 oracle development chain, unchanged.',
        prior='Condition original corpus-frequency prior on allowed word support per state, then factor into ending/within-ending probabilities for sharing. Inactive groups have zero prior mass.',
        oracle_init='Supervised counts plus support-conditioned prior; this is constrained complete-label MAP, not a projection claimed identical to old initial probabilities.',
        random_init='Original gamma(2)*corpus-frequency draws, masked and row-renormalized; same seeds.',
        evaluation='All/query plus ambiguous-word-only scores; oracle word-majority reference supplied separately. Within-arm objective selection only.'))
    results={};q,_,_=prior_data(obs['sequences'],obs['word_endings'])
    for arm in ('word','ending'):
        sharing=arm=='ending';initial=supported_update(counts,prior,sharing);print('Supported oracle',arm,flush=True)
        oracle=trajectory(chain,obs,truth,initial,prior,sharing,True);random=[]
        for seed in SEEDS:
            print('Supported random',arm,seed,flush=True);e=np.random.default_rng(seed).gamma(2.,1.,size=counts.shape)*q[None,:]*support
            random.append(dict(seed=seed,**trajectory(chain,obs,truth,e,prior,sharing)))
        results[arm]=dict(oracle=oracle,random=random);print(arm,'initial/final',oracle['trace'][0]['query'],oracle['trace'][-1]['query'],'ambiguous',oracle['trace'][0]['ambiguous_query'],oracle['trace'][-1]['ambiguous_query'],'converged',oracle['converged'],flush=True)
    save(OUT/'results.json',results)

if __name__=='__main__':run()
