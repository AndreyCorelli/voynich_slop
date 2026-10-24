"""Validate normalized mixture, matched starts, and recovery/harm accounting."""
import numpy as np
from benchmarks.grammar_soft_fallback_iteration32 import OUT,HARD,BASELINE,EXACT,PREVIOUS,RATES,EPSILONS,PRIMARY,MASK_SEEDS,SEEDS,MAX_ITER,TOL,load,save,digest,fit_run
from benchmarks.grammar_soft_fallback_iteration32_evaluate import pair,predict
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics
from voynich_smt.supported_emissions import supported_prior,supported_log_prior
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture,fallback_posteriors


def run():
    for path in (OUT/'manifest.json',HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);evaluation=load(OUT/'evaluation.json');checked=rows=replayed=0
    for filename in load(OUT/'fit-index.json'):
        c=load(OUT/filename);seed=c['mask_seed'];rate=c['rate'];eps=c['epsilon'];arm=c['arm'];sharing=arm=='ending';support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);prior=supported_prior(obs['sequences'],obs['word_endings'],support);gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset'])
        path=BASELINE/f'fits-{seed}-1.0-{arm}.json' if not rate else HARD/f'fits-{seed}-{rate}-{arm}.json';hard=load(path);hardpred=predict(chain,hard['random'][hard['selected']]['final_emissions'],obs)
        assert c['selected']==max(range(5),key=lambda i:c['random'][i]['trace'][-1]['objective']);assert [r['seed'] for r in c['random']]==list(SEEDS)
        report=next(r for r in evaluation['cells'] if r['mask_seed']==seed and r['rate']==rate and r['epsilon']==eps and r['arm']==arm)
        for i,trial in enumerate([c['oracle']]+c['random']):
            original=hard['oracle'] if not i else hard['random'][i-1];initial=np.array(trial['initial_component']);final=np.array(trial['final_component']);np.testing.assert_allclose(initial,original['initial_emissions'],atol=1e-15)
            for component in (initial,final):
                assert not component[~support].any();np.testing.assert_allclose(component.sum(axis=1),1)
                emission=mixture(component,q,eps);assert np.all(emission>0) and np.all(emission>=eps*q[None,:]);np.testing.assert_allclose(emission.sum(axis=1),1)
            t=trial['trace'];assert min(np.diff([r['objective'] for r in t]))>=-1e-6;rows+=len(t);gain=t[-1]['objective']-t[-2]['objective']
            assert trial['converged']==(gain<=TOL*max(1.,abs(t[-2]['objective'])))
            if not trial['converged']:assert t[-1]['iteration']==MAX_ITER
            emission=mixture(final,q,eps);ll,gamma=forward_backward(chain,emission,obs['sequences']);lp=supported_log_prior(final,prior,sharing);np.testing.assert_allclose([ll,lp,ll+lp],[t[-1][k] for k in ('log_likelihood','prior','objective')],atol=1e-8)
            pred=np.concatenate(gamma).argmax(axis=1);assert token_metrics(pred,gold,masks)==t[-1]['scores']
            usage=fallback_posteriors(final,q,eps,obs['sequences'],gamma);assert np.all((usage>=0)&(usage<=1))
            for name,mask in masks.items():
                expected=float(usage[mask].mean()) if mask.any() else None
                if expected is None:assert trial['fallback_use'][name] is None
                else:np.testing.assert_allclose(trial['fallback_use'][name],expected)
                # Independent counts, including previously excluded tokens now recoverable.
                m=t[-1]['scores'][name];assert m['tokens']==int(mask.sum()) and m['correct']==int((pred[mask]==gold[mask]).sum())
            if seed==MASK_SEEDS[0] and rate==.5 and eps==PRIMARY:
                replay=fit_run(chain,obs,gold,masks,initial,prior,q,eps,sharing)
                assert replay['converged']==trial['converged'] and len(replay['trace'])==len(t);np.testing.assert_allclose(replay['final_component'],final,atol=1e-10)
                for a,b in zip(replay['trace'],t):
                    np.testing.assert_allclose([a[k] for k in ('log_likelihood','prior','objective')],[b[k] for k in ('log_likelihood','prior','objective')],atol=1e-8);assert a['scores']==b['scores']
                replayed+=1
            if not i or i==c['selected']+1:
                name='oracle' if not i else 'selected';paired=pair(pred,hardpred,gold,masks);assert paired==report[name]['versus_hard']
                recovered=int((masks['excluded_query']&(pred==gold)).sum());assert recovered+paired['covered_query']['net_gain']==paired['all_query']['net_gain']
            checked+=1
    result=dict(cells=120,final_fit_checks=checked,monotonic_objective_rows=rows,full_trajectory_replays=replayed,normalized_mixtures=True,component_support_exact=True,matched_hard_initializations=True,recovery_and_harm_accounting=True,prior_hashes_valid=True,scope='Existing development only; reserved200 unscored')
    save(OUT/'validation.json',result);print(result)

if __name__=='__main__':run()
