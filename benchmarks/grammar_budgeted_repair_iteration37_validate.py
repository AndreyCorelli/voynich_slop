"""Audit frozen-base mixture, exact repair support, and recovery accounting."""
import numpy as np
from benchmarks.grammar_budgeted_repair_iteration37 import OUT,FULL,FITS,DATA,HARD,BASELINE,EXACT,SEEDS,EPSILON,PRIMARY,MAX_ITER,TOL,load,save,digest,fit_run
from benchmarks.grammar_budgeted_repair_iteration37_evaluate import predict,changes
from benchmarks.grammar_candidate_expansion_iteration36_evaluate import bootstrap
from voynich_smt.latent_cipher_classes import prior_data,forward_backward
from voynich_smt.fallback_emissions import mixture
from voynich_smt.candidate_expansion import expand
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics
from voynich_smt.budgeted_candidate_repair import repair_prior,anchored_emission,repair_log_prior
from voynich_smt.candidate_abstention import abstention_metrics


def run():
    for path in (OUT/'fit-freeze.json',OUT/'manifest.json',FULL/'verification-manifest.json',FITS/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);proposals=load(OUT/'proposals.json');gold=np.concatenate(truth);ids=np.concatenate(obs['sequences']);offset=sum(map(len,obs['sequences'][:obs['offset']]));query=np.arange(len(gold))>=offset;evaluation=load(OUT/'evaluation.json');checked=rows=replayed=0
    original=[p for p in load(FULL/'proposals.json') if p['k']==2];assert original==proposals
    for filename,report in zip(load(OUT/'fit-index.json'),evaluation['cells']):
        c=load(OUT/filename);seed=c['mask_seed'];rate=c['rate'];arm=c['arm'];budget=c['budget'];proposal=next(p for p in proposals if all(p[k]==c[k] for k in ('mask_seed','rate','arm','strategy')));support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);newpairs=expand(support,proposal['additions'])&~support;prior=repair_prior(q,newpairs);active=newpairs.any(axis=1)
        expected=newpairs*q[None,:];sums=expected.sum(axis=1,keepdims=True);expected=np.divide(expected,sums,out=np.zeros_like(expected),where=sums>0);np.testing.assert_allclose(prior,expected)
        old=load(FITS/f'fits-{seed}-{rate}-{EPSILON}-{arm}.json');base=mixture(old['random'][old['selected']]['final_component'],q,EPSILON);base_copy=base.copy();baseline=predict(chain,base,obs);_,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset']);covered=support[gold,ids];repaired_word=newpairs.any(axis=0)[ids]
        assert c['selected']==max(range(5),key=lambda j:c['runs'][j]['trace'][-1]['objective']);assert [r['seed'] for r in c['runs']]==list(SEEDS)
        for trial in c['runs']:
            initial=np.array(trial['initial_repair']);final=np.array(trial['final_repair']);init=np.random.default_rng(trial['seed']).gamma(2.,1.,size=prior.shape)*prior;s=init.sum(axis=1,keepdims=True);init=np.divide(init,s,out=np.zeros_like(init),where=s>0);np.testing.assert_allclose(initial,init,atol=1e-15)
            for repair in (initial,final):
                assert not repair[~newpairs].any();np.testing.assert_allclose(repair.sum(axis=1),active.astype(float));e=anchored_emission(base,repair,budget);np.testing.assert_allclose(e.sum(axis=1),1);assert np.all(e>0)
                untouched=~newpairs.any(axis=0)
                if untouched.any():np.testing.assert_allclose(e[:,untouched]/base[:,untouched],np.broadcast_to((1-budget*active)[:,None],e[:,untouched].shape),atol=1e-12)
                np.testing.assert_array_equal(anchored_emission(base,repair,0),base)
            t=trial['trace'];assert min(np.diff([r['objective'] for r in t]))>=-1e-6;rows+=len(t);gain=t[-1]['objective']-t[-2]['objective'];assert trial['converged']==(gain<=TOL*max(1.,abs(t[-2]['objective'])))
            if not trial['converged']:assert t[-1]['iteration']==MAX_ITER
            ll,gamma=forward_backward(chain,anchored_emission(base,final,budget),obs['sequences']);lp=repair_log_prior(final,prior);np.testing.assert_allclose([ll,lp,ll+lp],[t[-1][k] for k in ('log_likelihood','prior','objective')],atol=1e-8);pred=np.concatenate(gamma).argmax(axis=1);assert token_metrics(pred,gold,masks)==t[-1]['scores']
            if seed==3001 and rate==.5 and c['strategy']=='context' and budget==PRIMARY:
                replay=fit_run(chain,base,obs,gold,masks,initial,prior,budget);assert replay['converged']==trial['converged'] and len(replay['trace'])==len(t);np.testing.assert_allclose(replay['final_repair'],final,atol=1e-10)
                for a,b in zip(replay['trace'],t):
                    np.testing.assert_allclose([a[k] for k in ('log_likelihood','prior','objective')],[b[k] for k in ('log_likelihood','prior','objective')],atol=1e-8);assert a['scores']==b['scores']
                replayed+=1
            checked+=1
        np.testing.assert_array_equal(base,base_copy)
        pred=predict(chain,anchored_emission(base,c['runs'][c['selected']]['final_repair'],budget),obs);assert changes(pred,baseline,gold,query,covered,repaired_word)==report['changes'];assert report['changes']['corrected']-report['changes']['spoiled']==report['changes']['net']==sum(report['sentence_delta'])
        assert abstention_metrics(pred[query],gold[query],~covered[query],np.array(proposal['flagged'])[query])==report['abstention']
        freq=predict(chain,anchored_emission(base,prior,budget),obs);assert token_metrics(freq,gold,masks)==c['frequency_only_scores']==report['frequency_only']
    for summary in evaluation['summary']:
        rr=[r for r in evaluation['cells'] if all(r[k]==summary[k] for k in ('arm','rate','strategy','budget'))];assert summary['bootstrap']==bootstrap(rr)
    for comp in evaluation['comparisons']:
        a=sorted([r for r in evaluation['cells'] if r['arm']==comp['arm'] and r['rate']==comp['rate'] and r['strategy']=='context' and r['budget']==PRIMARY],key=lambda r:r['mask_seed']);b=sorted([r for r in evaluation['cells'] if r['arm']==comp['arm'] and r['rate']==comp['rate'] and r['strategy']=='random' and r['budget']==PRIMARY],key=lambda r:r['mask_seed']);diff=[dict(sentence_tokens=x['sentence_tokens'],sentence_delta=(np.array(x['sentence_delta'])-np.array(y['sentence_delta'])).tolist()) for x,y in zip(a,b)];assert comp['bootstrap']==bootstrap(diff)
    result=dict(cells=160,final_fit_checks=checked,monotonic_objective_rows=rows,full_trajectory_replays=replayed,frozen_base_and_zero_budget_checked=True,normalized_mixture_and_exact_repair_support=True,untargeted_emission_ratio_bound=True,frequency_only_control=True,bootstrap_replays=36,prior_hashes_valid=True,scope='Existing oracle-controlled development only; reserved200 unscored')
    save(OUT/'validation.json',result);print(result)

if __name__=='__main__':run()
