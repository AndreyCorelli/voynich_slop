"""Calibrate disagreement gates on old background, evaluate separate old queries."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_masked_context_iteration33 import OUT as PROBES,FITS,HARD,BASELINE,EXACT,PREVIOUS,RATES,EPSILONS,PRIMARY,MASK_SEEDS,load,save,digest
from voynich_smt.missing_class_support import missing_support,cohorts
from voynich_smt.context_override import signals,calibrate

OUT=PROBES.parent/'iteration34-v2'
GRID=dict(confidence=(.25,.35,.45,.55,.65,.75,.85,.95),ratio=(1.,1.5,2.,4.,8.))
RISK=.01


def slice_features(f,mask):return {k:np.asarray(v)[mask].tolist() for k,v in f.items()}


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for path in (PROBES/'verification-manifest.json',FITS/'verification-manifest.json',HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');ids=np.concatenate(obs['sequences']);gold=np.concatenate(truth);offset=sum(map(len,obs['sequences'][:obs['offset']]));features=[];label_records=[]
    for row,filename in zip(load(PROBES/'evaluation.json'),load(PROBES/'probe-index.json')):
        seed=row['mask_seed'];rate=row['rate'];support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);p=load(PROBES/filename)
        # Feature function receives no oracle distributions, neighboring labels,
        # gold token metadata, or declaration of which words were perturbed.
        f=signals(p['probabilities']['masked_hmm'],p['probabilities']['ordinary_hmm'],support,ids)
        features.append(dict(mask_seed=seed,rate=rate,epsilon=row['epsilon'],arm=row['arm'],features=f));label_records.append(dict(gold=gold.tolist(),excluded=(~support[gold,ids]).tolist()))
    paths=[Path(__file__),Path('src/voynich_smt/context_override.py'),PROBES/'verification-manifest.json',PROBES/'probe-index.json',PROBES/'evaluation.json',PREVIOUS/'observations.json',PREVIOUS/'observation-truth.json',EXACT/'support-truth.json',BASELINE/'schedules.json',HARD/'deletions.json']
    OUT.mkdir();save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},grid=GRID,risk_budget=RISK,primary_gate='outside',primary_epsilon=PRIMARY,
        scope='Previously inspected development only. Threshold calibration uses background200 (1579 tokens); scoring uses disjoint query40 (473 tokens). Upstream oracle support/chain and transductive fits still see corpus; this is not a fresh held-out benchmark.',
        features='Only target-masked HMM posterior, ordinary posterior, and supplied candidate mask. No oracle neighbors, excluded labels, perturbation flags, plaintext or word-specific policy.',
        gates='outside primary: differing cavity top class outside supplied candidates; disagreement secondary: any differing cavity top class. Confidence and cavity top/current probability ratio thresholds.',
        calibration='Pool all five perturbation seeds and both deletion levels within arm/epsilon. Maximize calibration net corrected-minus-spoiled, subject to <=1% spoiling of baseline-correct covered calibration tokens. Disabled option; ties fewer spoils, fewer overrides, stricter thresholds. Positive calibration gain required to enable.',
        caveat='Calibration scenarios reuse sentence IDs across perturbations; counts are scenario-token exposures, not independent samples. One pooled policy does not receive deletion rate.',
        evaluation='Excluded-class detection ROC/AP; overridden/corrected/spoiled/unchanged-wrong; recovery, covered false overrides; sentence-cluster bootstrap for query accuracy delta. One simultaneous local tag-edit pass, no model refit or iterative context update.'))
    save(OUT/'features.json',features);save(OUT/'feature-truth.json',label_records)
    calibration_mask=np.arange(len(gold))<offset;policies={}
    for arm in ('word','ending'):
        for epsilon in EPSILONS:
            records=[dict(features=slice_features(f['features'],calibration_mask),gold=np.asarray(y['gold'])[calibration_mask].tolist(),excluded=np.asarray(y['excluded'])[calibration_mask].tolist()) for f,y in zip(features,label_records) if f['arm']==arm and f['epsilon']==epsilon]
            for gate in ('outside','disagreement'):
                name=f'{arm}/{epsilon}/{gate}';policies[name]=calibrate(records,GRID,RISK,gate);print(name,policies[name],flush=True)
    save(OUT/'policies.json',policies);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    print('Policies frozen before query evaluation',flush=True)

if __name__=='__main__':run()
