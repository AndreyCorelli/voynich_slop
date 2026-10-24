"""Choose a fixed repair budget on background corrections and spoils only."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_budgeted_repair_iteration37 import OUT as MODELS,FULL,FITS,FLAGS,DATA,HARD,BASELINE,EXACT,BUDGETS,EPSILON,load,save,digest
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture
from voynich_smt.budgeted_candidate_repair import anchored_emission
from voynich_smt.repair_budget_selection import select_budget

OUT=MODELS.parent/'iteration38'
RISKS=(.001,.005,.01)
PRIMARY=.01


def predict(chain,emission,obs):return np.concatenate(forward_backward(chain,emission,obs['sequences'])[1]).argmax(axis=1).tolist()


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for path in (MODELS/'verification-manifest.json',FULL/'verification-manifest.json',FITS/'verification-manifest.json',FLAGS/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];gold=np.concatenate(truth);offset=sum(map(len,obs['sequences'][:obs['offset']]));q,_,_=prior_data(obs['sequences'],obs['word_endings']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];cases=[]
    for proposal in load(MODELS/'proposals.json'):
        seed=proposal['mask_seed'];rate=proposal['rate'];arm=proposal['arm'];strategy=proposal['strategy'];old=load(FITS/f'fits-{seed}-{rate}-{EPSILON}-{arm}.json');base=mixture(old['random'][old['selected']]['final_component'],q,EPSILON);baseline=predict(chain,base,obs);predictions={'0.0':baseline}
        for budget in BUDGETS:
            fit=load(MODELS/f'fits-{seed}-{rate}-{arm}-{strategy}-{budget}.json');repair=fit['runs'][fit['selected']]['final_repair'];predictions[str(budget)]=predict(chain,anchored_emission(base,repair,budget),obs)
        cases.append(dict(**{k:proposal[k] for k in ('mask_seed','rate','arm','strategy')},baseline=baseline,predictions=predictions,flagged=proposal['flagged']))
    OUT.mkdir();save(OUT/'predictions.json',cases)
    paths=[Path(__file__),Path('src/voynich_smt/repair_budget_selection.py'),MODELS/'verification-manifest.json',MODELS/'proposals.json',FULL/'verification-manifest.json',FITS/'verification-manifest.json',FLAGS/'verification-manifest.json',DATA/'observations.json',DATA/'observation-truth.json',BASELINE.parent/'iteration28/chains.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},risks=RISKS,primary_risk=PRIMARY,budgets=(0.,)+BUDGETS,
        scope='Reanalysis of frozen iteration37 models on existing background200/query40 split. Query outcomes for budgets were previously inspected; new selection uses background labels only, not independent confirmation. No new fits/fresh/reserve scoring.',
        calibration='Pool five perturbations and both deletion rates within each old-model arm and proposal strategy. Maximize background net corrected-minus-spoiled, with spoiled <=risk*all baseline-correct background tags. Include no-update budget0; ties fewer spoils then smaller budget.',
        controls='Random K2 proposals calibrated identically, and risk.001/.005 sensitivity. Start selection remains original unlabeled objective selection; no cross-budget objective ranking or query budget selection.',
        interpretation='Empirical background spoil budget is not a query guarantee. Old emissions frozen as components, upstream oracle support/chain and transductive fitting retained. Original abstention flags fixed.'))
    policies={}
    for arm in ('word','ending'):
        for strategy in ('context','random'):
            records=[dict(baseline=r['baseline'][:offset],predictions={b:p[:offset] for b,p in r['predictions'].items()},gold=gold[:offset].tolist()) for r in cases if r['arm']==arm and r['strategy']==strategy]
            for risk in RISKS:
                key=f'{arm}/{strategy}/{risk}';policies[key]=select_budget(records,risk);print(key,policies[key]['budget'],policies[key]['calibration'],flush=True)
    save(OUT/'policies.json',policies);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));print('12 policies frozen before applying selections to query evaluation',flush=True)

if __name__=='__main__':run()
