"""Independent budget selection and query spoil accounting."""
import numpy as np
from benchmarks.grammar_calibrated_repair_iteration38 import OUT,MODELS,FITS,FLAGS,DATA,BASELINE,EXACT,HARD,RISKS,PRIMARY,BUDGETS,EPSILON,load,save,digest
from benchmarks.grammar_calibrated_repair_iteration38_evaluate import pool
from benchmarks.grammar_candidate_expansion_iteration36_evaluate import bootstrap
from voynich_smt.repair_budget_selection import select_budget,edit_counts
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture
from voynich_smt.budgeted_candidate_repair import anchored_emission


def predict(chain,emission,obs):return np.concatenate(forward_backward(chain,emission,obs['sequences'])[1]).argmax(axis=1)


def run():
    for filename in (OUT/'evaluation-freeze.json',OUT/'manifest.json',MODELS/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];gold=np.concatenate(truth);offset=sum(map(len,obs['sequences'][:obs['offset']]));data=load(DATA/'datasets.json');a={s['sent_id'] for s in data['background_calibration']};b={s['sent_id'] for s in data['calibration']};assert len(a)==200 and len(b)==40 and not a&b
    q,_,_=prior_data(obs['sequences'],obs['word_endings']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];cases=load(OUT/'predictions.json');policies=load(OUT/'policies.json');evaluation=load(OUT/'evaluation.json');prediction_checks=0
    for case in cases:
        seed=case['mask_seed'];rate=case['rate'];arm=case['arm'];strategy=case['strategy'];old=load(FITS/f'fits-{seed}-{rate}-{EPSILON}-{arm}.json');base=mixture(old['random'][old['selected']]['final_component'],q,EPSILON);baseline=predict(chain,base,obs);np.testing.assert_array_equal(baseline,case['baseline']);np.testing.assert_array_equal(baseline,case['predictions']['0.0']);prediction_checks+=1
        for budget in BUDGETS:
            fit=load(MODELS/f'fits-{seed}-{rate}-{arm}-{strategy}-{budget}.json');selected=fit['runs'][fit['selected']];pred=predict(chain,anchored_emission(base,selected['final_repair'],budget),obs);np.testing.assert_array_equal(pred,case['predictions'][str(budget)]);prediction_checks+=1
    policy_checks=0
    for arm in ('word','ending'):
        for strategy in ('context','random'):
            records=[dict(baseline=r['baseline'][:offset],predictions={bb:p[:offset] for bb,p in r['predictions'].items()},gold=gold[:offset].tolist()) for r in cases if r['arm']==arm and r['strategy']==strategy]
            for risk in RISKS:
                p=policies[f'{arm}/{strategy}/{risk}'];assert p==select_budget(records,risk)
                # Independent enumeration: directly count pooled old/new correctness.
                options=[]
                for budget in (0.,)+BUDGETS:
                    corrected=spoiled=correct=0
                    for r in records:
                        old=np.array(r['baseline'])==np.array(r['gold']);new=np.array(r['predictions'][str(budget)])==np.array(r['gold']);corrected+=int((~old&new).sum());spoiled+=int((old&~new).sum());correct+=int(old.sum())
                    if spoiled<=risk*correct:options.append((corrected-spoiled,-spoiled,-budget,budget))
                assert p['budget']==max(options)[-1];assert p['calibration']['spoiled']<=risk*p['calibration']['baseline_correct'];policy_checks+=1
    for row in evaluation['cells']:
        case=next(c for c in cases if all(c[k]==row[k] for k in ('mask_seed','rate','arm','strategy')));budget=policies[f"{row['arm']}/{row['strategy']}/{row['risk']}"]['budget'];assert row['budget']==budget;pred=np.array(case['predictions'][str(budget)])[offset:];baseline=np.array(case['baseline'])[offset:];y=gold[offset:];np.testing.assert_array_equal(pred,row['query_prediction']);counts=edit_counts(baseline,pred,y)
        for k,v in counts.items():assert row['counts'][k]==v
        assert counts['net']==sum(row['sentence_delta'])==int((pred==y).sum()-(baseline==y).sum())
        if budget==0:assert counts['net']==counts['corrected']==counts['spoiled']==0
    for summary in evaluation['summary']:
        rr=[r for r in evaluation['cells'] if all(r[k]==summary[k] for k in ('arm','strategy','risk')) and (summary['rate']=='pooled' or r['rate']==summary['rate'])];assert summary['pooled']==pool(rr);assert summary['bootstrap']==bootstrap(rr)
    for comparison in evaluation['comparisons']:
        aa=sorted([r for r in evaluation['cells'] if r['arm']==comparison['arm'] and r['rate']==comparison['rate'] and r['strategy']=='context' and r['risk']==PRIMARY],key=lambda r:r['mask_seed']);bb=sorted([r for r in evaluation['cells'] if r['arm']==comparison['arm'] and r['rate']==comparison['rate'] and r['strategy']=='random' and r['risk']==PRIMARY],key=lambda r:r['mask_seed']);diff=[dict(sentence_tokens=x['sentence_tokens'],sentence_delta=(np.array(x['sentence_delta'])-np.array(y['sentence_delta'])).tolist()) for x,y in zip(aa,bb)];assert comparison['bootstrap']==bootstrap(diff)
    report=dict(frozen_model_prediction_replays=prediction_checks,policy_replays=policy_checks,independent_budget_optimality_checks=policy_checks,query_policy_audits=len(evaluation['cells']),pooled_bootstrap_replays=40,calibration_query_ids_disjoint=True,no_update_control=True,prior_hashes_valid=True,scope='Previously inspected background200/query40; prior budget query outcomes known; no independent confirmation or reserved scoring')
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
