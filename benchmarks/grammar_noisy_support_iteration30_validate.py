"""Validate masks and all fits; replay twelve hardest-cell trajectories."""
import numpy as np
from benchmarks.grammar_noisy_support_iteration30 import OUT,EXACT,BASELINE,PREVIOUS,RATES,MASK_SEEDS,SEEDS,MAX_ITER,TOL,load,save,digest,metrics,fit_run
from benchmarks.grammar_noisy_support_iteration30_evaluate import candidate_baselines
from voynich_smt.noisy_class_support import support_schedule,noisy_support
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_log_prior
from voynich_smt.latent_cipher_classes import forward_backward,prior_data


def run():
    for filename in (OUT/'manifest.json',EXACT/'verification-manifest.json',BASELINE/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'schedules.json')==load(OUT/'manifest.json')['schedules_hash']
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);counts=np.array(load(EXACT/'support-truth.json')['gold_counts']);chain=load(BASELINE/'chains.json')['oracle_development'];schedules=load(OUT/'schedules.json');evaluation=load(OUT/'evaluation.json');q,_,_=prior_data(obs['sequences'],obs['word_endings'])
    for seed in MASK_SEEDS:
        assert schedules[str(seed)]==support_schedule(reference,seed);previous=reference
        for rate in RATES:
            support,affected=noisy_support(reference,schedules[str(seed)],rate)
            assert np.all(support[previous]) and np.all(support[reference]);assert affected.sum()==int(rate*reference.shape[1]);assert (support&~reference).sum()==affected.sum();previous=support
    checked=replayed=trace_rows=0
    for filename in load(OUT/'fit-index.json'):
        cell=load(OUT/filename);support,affected=noisy_support(reference,schedules[str(cell['mask_seed'])],cell['rate']);prior=supported_prior(obs['sequences'],obs['word_endings'],support);sharing=cell['arm']=='ending'
        assert cell['selected']==max(range(5),key=lambda i:cell['random'][i]['trace'][-1]['objective'])
        assert [r['seed'] for r in cell['random']]==list(SEEDS)
        report=next(c for c in evaluation['cells'] if c['mask_seed']==cell['mask_seed'] and c['rate']==cell['rate'] and c['arm']==cell['arm'])
        assert report['baselines']==candidate_baselines(chain,obs,truth,reference,support,affected)
        for i,trial in enumerate([cell['oracle']]+cell['random']):
            initial=np.array(trial['initial_emissions']);final=np.array(trial['final_emissions'])
            expected=supported_update(counts,prior,sharing) if i==0 else np.random.default_rng(trial['seed']).gamma(2.,1.,size=counts.shape)*q[None,:]*support
            expected/=expected.sum(axis=1,keepdims=True);np.testing.assert_allclose(initial,expected,atol=1e-15)
            for e in (initial,final):assert not e[~support].any();np.testing.assert_allclose(e.sum(axis=1),1)
            trace=trial['trace'];assert min(np.diff([r['objective'] for r in trace]))>=-1e-6;trace_rows+=len(trace)
            gain=trace[-1]['objective']-trace[-2]['objective'];assert trial['converged']==(gain<=TOL*max(1,abs(trace[-2]['objective'])))
            if not trial['converged']:assert trace[-1]['iteration']==MAX_ITER
            ll,gamma=forward_backward(chain,final,obs['sequences']);lp=supported_log_prior(final,prior,sharing)
            np.testing.assert_allclose([ll,lp,ll+lp],[trace[-1]['log_likelihood'],trace[-1]['prior'],trace[-1]['objective']],atol=1e-8)
            scored=metrics(gamma,truth,obs,reference,affected);assert all(scored[k]==trace[-1][k] for k in scored)
            # Independent flatten-and-filter accuracy checks for every cohort.
            pred=np.concatenate(gamma).argmax(axis=1);gold=np.concatenate(truth);ids=np.concatenate(obs['sequences']);offset=sum(map(len,obs['sequences'][:obs['offset']]))
            for cohort,mask in [('all',np.ones(reference.shape[1],bool)),('affected',affected),('originally_ambiguous',reference.sum(axis=0)>1),('affected_singletons',affected&(reference.sum(axis=0)==1))]:
                for suffix,start in [('',0),('_query',offset)]:
                    selected=mask[ids[start:]];m=trace[-1][cohort+suffix];assert m['tokens']==int(selected.sum());assert m['correct']==int((pred[start:][selected]==gold[start:][selected]).sum())
            if cell['mask_seed']==MASK_SEEDS[0] and cell['rate']==1.:
                replay=fit_run(chain,obs,truth,reference,affected,initial,prior,sharing)
                assert replay['converged']==trial['converged'] and replay['first_net_loss']==trial['first_net_loss']
                assert len(replay['trace'])==len(trial['trace'])
                np.testing.assert_allclose(replay['final_emissions'],final,atol=1e-10)
                for a,b in zip(replay['trace'],trial['trace']):
                    np.testing.assert_allclose([a[k] for k in ('log_likelihood','prior','objective')],[b[k] for k in ('log_likelihood','prior','objective')],atol=1e-8)
                    assert all(a[k]==b[k] for k in scored)
                replayed+=1
            checked+=1
    report=dict(cells=60,final_fit_checks=checked,monotonic_trace_rows=trace_rows,full_trajectory_replays=replayed,nested_masks_valid=True,all_gold_candidates_retained=True,independent_cohort_counts=True,prior_hashes_valid=True,scope='Existing development only; reserve untouched')
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
