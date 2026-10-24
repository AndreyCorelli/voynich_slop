"""Calibrate candidate-quality flags on background; query scoring separate."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_context_override_iteration34 import OUT as PREVIOUS,PROBES,PREVIOUS as DATA,EPSILONS,load,save,digest
from voynich_smt.candidate_abstention import calibrate_flag

OUT=PREVIOUS.parent/'iteration35'
BUDGETS=(.01,.05,.10)
PRIMARY=.01
SCORES=('outside_mass','ordinary_uncertainty')


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for path in (PREVIOUS/'verification-manifest.json',PROBES/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];offset=sum(map(len,obs['sequences'][:obs['offset']]));features=load(PREVIOUS/'features.json');truth=load(PREVIOUS/'feature-truth.json');records=[]
    for f,y,filename in zip(features,truth,load(PROBES/'probe-index.json')):
        p=load(PROBES/filename);uncertainty=1-np.asarray(p['probabilities']['ordinary_hmm']).max(axis=1)
        records.append(dict(**{k:f[k] for k in ('mask_seed','rate','epsilon','arm')},predicted=f['features']['old'],scores=dict(outside_mass=f['features']['outside_mass'],ordinary_uncertainty=uncertainty.tolist())))
    paths=[Path(__file__),Path('src/voynich_smt/candidate_abstention.py'),PREVIOUS/'verification-manifest.json',PREVIOUS/'features.json',PREVIOUS/'feature-truth.json',PROBES/'verification-manifest.json',PROBES/'probe-index.json',DATA/'observations.json']
    OUT.mkdir();save(OUT/'observations.json',records)
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},budgets=BUDGETS,primary_budget=PRIMARY,primary_epsilon=.01,primary_score='outside_mass',
        scope='Internal previously inspected development200 background/40 query split. Upstream oracle candidate support, oracle chain, and transductive parameters retained; no fresh or reserved scoring.',
        selection='Within arm/epsilon pool both deletion rates and five perturbation seeds. Choose scalar >=threshold maximizing background excluded detections with <=budget false flags on baseline-correct covered tokens; whole tie groups, ties fewer flags. No positive detection gain means disabled.',
        controls='Same calibration and budgets for ordinary posterior uncertainty 1-max(p), plus random-abstention expected accuracy equal to baseline at matched coverage.',
        evaluation='Flag precision/recall for excluded tags; false flags on correct covered tags; retained tag accuracy/coverage and fraction of all tokens still correct. No tag changes, model refits, or grammatical parse claims.',
        caveat='Calibration repeated scenarios are not independent tokens. Query sentences previously inspected; fixed scalar budgets sensitivity, no query threshold selection.'))
    policies={}
    for arm in ('word','ending'):
        for epsilon in EPSILONS:
            selected=[(r,y) for r,y in zip(records,truth) if r['arm']==arm and r['epsilon']==epsilon]
            excluded=np.concatenate([np.asarray(y['excluded'])[:offset] for r,y in selected]);protected=np.concatenate([(np.asarray(r['predicted'])[:offset]==np.asarray(y['gold'])[:offset])&~np.asarray(y['excluded'])[:offset] for r,y in selected])
            for score in SCORES:
                values=np.concatenate([r['scores'][score][:offset] for r,y in selected])
                for budget in BUDGETS:
                    name=f'{arm}/{epsilon}/{score}/{budget}';policies[name]=calibrate_flag(values,excluded,protected,budget);print(name,policies[name],flush=True)
    save(OUT/'policies.json',policies);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));print('24 flag policies frozen before query evaluation',flush=True)

if __name__=='__main__':run()
