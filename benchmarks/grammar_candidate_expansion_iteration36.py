"""Candidate repair from frozen flags, with capped and matched random proposals."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_candidate_abstention_iteration35 import OUT as FLAGS,PREVIOUS as FEATURE_SOURCE,PROBES,DATA,load,save,digest
from benchmarks.grammar_soft_fallback_iteration32 import OUT as FITS,HARD,BASELINE,EXACT,SEEDS,MAX_ITER,TOL,fit_run
from voynich_smt.latent_cipher_classes import prior_data
from voynich_smt.supported_emissions import supported_prior
from voynich_smt.missing_class_support import missing_support,cohorts
from voynich_smt.candidate_abstention import flag
from voynich_smt.candidate_expansion import propose,expand

OUT=FLAGS.parent/'iteration36'
SETTINGS=(('context',1),('context',2),('context',3),('random',2))
EPSILON=.01
BUDGET=.01
WARM_MASS=.01


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for path in (FLAGS/'verification-manifest.json',PROBES/'verification-manifest.json',FITS/'verification-manifest.json',HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');policies=load(FLAGS/'policies.json');flag_records=load(FLAGS/'observations.json');ids=np.concatenate(obs['sequences']);q,_,_=prior_data(obs['sequences'],obs['word_endings']);proposals=[]
    for r,filename in zip(flag_records,load(PROBES/'probe-index.json')):
        if r['epsilon']!=EPSILON:continue
        seed=r['mask_seed'];rate=r['rate'];arm=r['arm'];support,_=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);policy=policies[f'{arm}/{EPSILON}/outside_mass/{BUDGET}'];flagged=flag(r['scores']['outside_mass'],policy);context=load(PROBES/filename)['probabilities']['masked_hmm']
        for strategy,k in SETTINGS:
            repair=propose(support,ids,context,flagged,k,strategy,36000+seed)
            proposals.append(dict(mask_seed=seed,rate=rate,arm=arm,strategy=strategy,k=k,additions=repair,flagged=flagged.tolist()))
    OUT.mkdir();save(OUT/'proposals.json',proposals)
    paths=[Path(__file__),Path('src/voynich_smt/candidate_expansion.py'),Path('src/voynich_smt/fallback_emissions.py'),Path('src/voynich_smt/supported_emissions.py'),Path('benchmarks/grammar_soft_fallback_iteration32.py'),FLAGS/'verification-manifest.json',FLAGS/'policies.json',FLAGS/'observations.json',PROBES/'verification-manifest.json',PROBES/'probe-index.json',FITS/'verification-manifest.json',HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',DATA/'observations.json',DATA/'observation-truth.json',EXACT/'support-truth.json',BASELINE/'schedules.json',HARD/'deletions.json',BASELINE.parent/'iteration28/chains.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},proposals_hash=digest(OUT/'proposals.json'),settings=SETTINGS,primary=['context',2],epsilon=EPSILON,flag_budget=BUDGET,warm_mass=WARM_MASS,seeds=SEEDS,max_iter=MAX_ITER,tolerance=TOL,
        scope='Same inspected development200 background/40 queries. Frozen iteration35 flag policy; oracle chain and initial candidate metadata remain privileged. No fresh/reserve scoring.',
        proposal='Apply fixed flags to all unlabeled background+query observations. For each flagged word, average each flagged occurrence cavity posterior conditioned outside its current support; add topK classes with class-index tie breaks. Total additions capped per word, no label input.',
        controls='K1/K3 sensitivity; K2 uniformly random outside additions to exactly same words, per-mask seed36000+seed. No selection by query accuracy or cross-mask objective.',
        refit='Same epsilon=.01 mixture and chain; support-conditioned priors recomputed. Five matched random starts selected by within-cell objective; separate warm start (1-.01)*old component+.01*new support prior to open new cells with finite log prior. No supervised repair initialization.',
        evaluation='New/false candidate pairs, original-excluded token coverage gained, class accuracy and losses on originally covered tokens. Original abstention flags fixed; no reflagging or recursive proposal updates.'))
    save(OUT/'fit-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));index=[]
    for proposal in proposals:
        seed=proposal['mask_seed'];rate=proposal['rate'];arm=proposal['arm'];sharing=arm=='ending';support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);enlarged=expand(support,proposal['additions']);prior=supported_prior(obs['sequences'],obs['word_endings'],enlarged)
        # Score on the original missing/covered cohorts, not relabeled repair cohorts.
        gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset']);old=load(FITS/f'fits-{seed}-{rate}-{EPSILON}-{arm}.json');component=np.array(old['random'][old['selected']]['final_component']);initial=(1-WARM_MASS)*component+WARM_MASS*prior['word']
        print('Expansion',seed,rate,arm,proposal['strategy'],proposal['k'],flush=True);warm=fit_run(chain,obs,gold,masks,initial,prior,q,EPSILON,sharing);random=[]
        for init_seed in SEEDS:
            initial=np.random.default_rng(init_seed).gamma(2.,1.,size=enlarged.shape)*q[None,:]*enlarged
            random.append(dict(seed=init_seed,**fit_run(chain,obs,gold,masks,initial,prior,q,EPSILON,sharing)))
        selected=max(range(5),key=lambda i:random[i]['trace'][-1]['objective']);filename=f"fits-{seed}-{rate}-{arm}-{proposal['strategy']}-{proposal['k']}.json"
        save(OUT/filename,dict(**{k:proposal[k] for k in ('mask_seed','rate','arm','strategy','k')},selected=selected,warm=warm,random=random));index.append(filename)
    save(OUT/'fit-index.json',index);print('Saved',len(index),'cells /',len(index)*6,'fits',flush=True)

if __name__=='__main__':run()
