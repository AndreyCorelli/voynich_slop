"""Repeat oracle-start EM with development-oracle fixed transitions."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_oracle_emission_challenge_iteration27 import PREVIOUS,OUT as BASELINE,SEEDS,MAX_ITER,TOL,load,save,digest,trajectory
from voynich_smt.latent_cipher_classes import fixed_chain,oracle_emissions,prior_data

OUT=PREVIOUS.parent/'iteration28'


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for manifest in (PREVIOUS/'verification-manifest.json',BASELINE/'verification-manifest.json'):
        for p,h in load(manifest)['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration']
    source=load(PREVIOUS/'source-models.json')['chains']['pooled'];chain=fixed_chain(truth,8,alpha=.5)
    inputs=[Path(__file__),Path('src/voynich_smt/latent_cipher_classes.py'),Path('src/voynich_smt/oracle_emission_challenge.py'),Path('benchmarks/grammar_oracle_emission_challenge_iteration27.py'),PREVIOUS/'verification-manifest.json',BASELINE/'verification-manifest.json',BASELINE/'results.json',PREVIOUS/'observations.json',PREVIOUS/'observation-truth.json']
    OUT.mkdir();save(OUT/'chains.json',dict(source=source,oracle_development=chain))
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in inputs},chains_hash=digest(OUT/'chains.json'),
        scope='Already inspected calibration40/background200 only: 240 sentences, 2052 tokens. No fresh target or reserved scoring.',
        change='Replace source start/transition/termination probabilities with smoothed counts of the exact development reference class sequences. Fix these throughout EM.',
        privileged='Oracle transitions and supervised emission initialization use the same development labels; this is an in-sample diagnostic upper bound, not deployable training.',
        controlled='Emission initialization, priors, observations, five random seeds, cap, tolerance, EM algorithm, and scoring match iteration27; source trajectories reused unchanged.',
        alpha=.5,max_iter=MAX_ITER,tolerance=TOL,seeds=SEEDS,arms=['word','ending'],selection='Maximum objective within each chain/arm only, never target accuracy. No cross-chain likelihood ranking.',
        interpretation='Persistence of drift rules out source-domain mismatch as a sufficient explanation for this HMM; it does not isolate higher-order context from smoothing, ambiguity, or latent identifiability.'))
    results={}
    for arm in ('word','ending'):
        sharing=arm=='ending';initial=oracle_emissions(chain,obs['sequences'],obs['word_endings'],truth,sharing)
        old=load(BASELINE/'results.json')[arm]['oracle']['initial_emissions'];np.testing.assert_allclose(initial,old,atol=1e-15)
        print('Oracle chain/oracle start',arm,flush=True);oracle=trajectory(chain,obs,truth,initial,sharing,True);random=[]
        q,_,_=prior_data(obs['sequences'],obs['word_endings'])
        for seed in SEEDS:
            print('Oracle chain/random',arm,seed,flush=True);e=np.random.default_rng(seed).gamma(2.,1.,size=initial.shape)*q[None,:]
            random.append(dict(seed=seed,**trajectory(chain,obs,truth,e,sharing)))
        results[arm]=dict(oracle=oracle,random=random)
        print(arm,'initial',oracle['trace'][0]['query'],'final',oracle['trace'][-1]['query'],'converged',oracle['converged'],'first_loss',oracle['first_corruption']['iteration'] if oracle['first_corruption'] else None,flush=True)
    save(OUT/'results.json',results)

if __name__=='__main__':run()
