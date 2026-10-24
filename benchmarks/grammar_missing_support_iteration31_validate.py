"""Audit coverage ceilings, error accounting, and matched spillover."""
import numpy as np
from benchmarks.grammar_missing_support_iteration31 import OUT,BASELINE,EXACT,PREVIOUS,RATES,MASK_SEEDS,SEEDS,MAX_ITER,TOL,load,save,digest,fit_run
from benchmarks.grammar_missing_support_iteration31_evaluate import predict,summarize_pair
from voynich_smt.missing_class_support import deletion_schedule,missing_support,cohorts
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_log_prior
from voynich_smt.latent_cipher_classes import forward_backward,prior_data


def run():
    for path in (OUT/'manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'deletions.json')==load(OUT/'manifest.json')['deletions_hash']
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];st=load(EXACT/'support-truth.json');reference=np.array(st['support']);counts=np.array(st['gold_counts']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(OUT/'deletions.json');evaluation=load(OUT/'evaluation.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);baseline_predictions={}
    for seed in MASK_SEEDS:
        assert deletions[str(seed)]==deletion_schedule(reference,seed+100)
        last=None
        for rate in (0,)+RATES:
            support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate)
            assert support.any(axis=0).all() and support.any(axis=1).all()
            assert int((reference&~support).sum())==int(rate*reference.shape[1]);assert affected.sum()==int(rate*reference.shape[1])
            if last is not None:assert np.all(last[support])
            last=support
        for arm in ('word','ending'):
            b=load(BASELINE/f'fits-{seed}-1.0-{arm}.json');baseline_predictions[seed,arm]=predict(chain,b['random'][b['selected']]['final_emissions'],obs)
    checked=rows=replayed=0;offset=sum(map(len,obs['sequences'][:obs['offset']]));gold=np.concatenate(truth);ids=np.concatenate(obs['sequences'])
    for filename in load(OUT/'fit-index.json'):
        c=load(OUT/filename);seed=c['mask_seed'];arm=c['arm'];sharing=arm=='ending';support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],c['rate']);prior=supported_prior(obs['sequences'],obs['word_endings'],support);y,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset'])
        np.testing.assert_array_equal(gold,y);np.testing.assert_array_equal(masks['covered'],support[gold,ids])
        assert c['selected']==max(range(5),key=lambda i:c['random'][i]['trace'][-1]['objective']);assert [r['seed'] for r in c['random']]==list(SEEDS)
        report=next(r for r in evaluation['cells'] if r['mask_seed']==seed and r['rate']==c['rate'] and r['arm']==arm)
        for i,trial in enumerate([c['oracle']]+c['random']):
            initial=np.array(trial['initial_emissions']);final=np.array(trial['final_emissions']);expected=supported_update(counts*support,prior,sharing) if not i else np.random.default_rng(trial['seed']).gamma(2.,1.,size=counts.shape)*q[None,:]*support
            expected/=expected.sum(axis=1,keepdims=True);np.testing.assert_allclose(initial,expected,atol=1e-15)
            for e in (initial,final):assert not e[~support].any();np.testing.assert_allclose(e.sum(axis=1),1)
            t=trial['trace'];assert min(np.diff([r['objective'] for r in t]))>=-1e-6;rows+=len(t)
            gain=t[-1]['objective']-t[-2]['objective'];assert trial['converged']==(gain<=TOL*max(1.,abs(t[-2]['objective'])))
            if not trial['converged']:assert t[-1]['iteration']==MAX_ITER
            ll,gamma=forward_backward(chain,final,obs['sequences']);lp=supported_log_prior(final,prior,sharing);np.testing.assert_allclose([ll,lp,ll+lp],[t[-1][k] for k in ('log_likelihood','prior','objective')],atol=1e-8)
            pred=np.concatenate(gamma).argmax(axis=1)
            for name,mask in masks.items():
                m=t[-1]['scores'][name];assert m['tokens']==int(mask.sum()) and m['correct']==int((pred[mask]==gold[mask]).sum())
            assert t[-1]['scores']['excluded']['correct']==0
            assert t[-1]['scores']['all_query']['correct']<=int(masks['covered_query'].sum())
            if seed==MASK_SEEDS[0] and c['rate']==.5:
                replay=fit_run(chain,obs,gold,masks,initial,prior,sharing)
                assert replay['converged']==trial['converged'] and len(replay['trace'])==len(t);np.testing.assert_allclose(replay['final_emissions'],final,atol=1e-10)
                for a,b in zip(replay['trace'],t):
                    np.testing.assert_allclose([a[k] for k in ('log_likelihood','prior','objective')],[b[k] for k in ('log_likelihood','prior','objective')],atol=1e-8);assert a['scores']==b['scores']
                replayed+=1
            checked+=1
        for name,trial in [('selected',c['random'][c['selected']]),('oracle',c['oracle'])]:
            pred=predict(chain,trial['final_emissions'],obs);pair=summarize_pair(pred,baseline_predictions[seed,arm],gold,masks);assert pair==report[name]
            errors=pair['query_error_decomposition'];assert errors['unavoidable']+errors['covered_errors']==errors['total']
            for cohort in masks:
                a=pair['scores'][cohort];b=pair['baseline'][cohort];assert b['correct']-a['correct']==pair['paired'][cohort]['net_harm']
    report=dict(cells=60,final_fit_checks=checked,monotonic_objective_rows=rows,full_trajectory_replays=replayed,nested_nonempty_masks=True,exact_coverage_ceilings=True,independent_token_cohorts=True,matched_baseline_and_error_accounting=True,prior_hashes_valid=True,scope='Previously inspected development only; reserve200 unscored')
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
