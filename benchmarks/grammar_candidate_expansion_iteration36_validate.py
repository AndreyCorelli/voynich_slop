"""Replay proposal construction, retrieval accounting, and expanded-support EM."""
import numpy as np
from benchmarks.grammar_candidate_expansion_iteration36 import OUT,FLAGS,PROBES,DATA,FITS,HARD,BASELINE,EXACT,SEEDS,EPSILON,WARM_MASS,SETTINGS,load,save,digest,fit_run
from benchmarks.grammar_candidate_expansion_iteration36_evaluate import predict,bootstrap
from voynich_smt.latent_cipher_classes import prior_data,forward_backward
from voynich_smt.supported_emissions import supported_prior,supported_log_prior
from voynich_smt.fallback_emissions import mixture
from voynich_smt.candidate_abstention import flag,abstention_metrics
from voynich_smt.candidate_expansion import propose,expand
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics


def run():
    for filename in (OUT/'fit-freeze.json',OUT/'manifest.json',FLAGS/'verification-manifest.json',PROBES/'verification-manifest.json',FITS/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'proposals.json')==load(OUT/'manifest.json')['proposals_hash']
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');policies=load(FLAGS/'policies.json');flagrecords=load(FLAGS/'observations.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);gold=np.concatenate(truth);ids=np.concatenate(obs['sequences']);offset=sum(map(len,obs['sequences'][:obs['offset']]));query=np.arange(len(gold))>=offset;proposals=load(OUT/'proposals.json');evaluation=load(OUT/'evaluation.json');checked=rows=replayed=0;constructed=0
    for proposal,filename,report in zip(proposals,load(OUT/'fit-index.json'),evaluation['cells']):
        seed=proposal['mask_seed'];rate=proposal['rate'];arm=proposal['arm'];sharing=arm=='ending';i=next(i for i,r in enumerate(flagrecords) if r['mask_seed']==seed and r['rate']==rate and r['arm']==arm and r['epsilon']==EPSILON);flagrecord=flagrecords[i];prob=load(PROBES/load(PROBES/'probe-index.json')[i]);support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);flagged=flag(flagrecord['scores']['outside_mass'],policies[f'{arm}/{EPSILON}/outside_mass/0.01'])
        np.testing.assert_array_equal(flagged,proposal['flagged']);expected=propose(support,ids,prob['probabilities']['masked_hmm'],flagged,proposal['k'],proposal['strategy'],36000+seed);assert expected==proposal['additions'];constructed+=1
        enlarged=expand(support,expected);assert np.all(enlarged[support]);newpairs=enlarged&~support
        for w,cc in expected.items():assert len(cc)<=proposal['k'] and not support[cc,int(w)].any() and np.any(flagged&(ids==int(w)))
        # Matched random additions have the exact same word set and per-word cap.
        if proposal['k']==2:
            other=next(p for p in proposals if p['mask_seed']==seed and p['rate']==rate and p['arm']==arm and p['k']==2 and p['strategy']!=proposal['strategy']);assert {w:len(cc) for w,cc in expected.items()}=={w:len(cc) for w,cc in other['additions'].items()}
        prior=supported_prior(obs['sequences'],obs['word_endings'],enlarged);_,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset']);fit=load(OUT/filename);old=load(FITS/f'fits-{seed}-{rate}-{EPSILON}-{arm}.json');oldcomponent=np.array(old['random'][old['selected']]['final_component']);baseline=predict(chain,oldcomponent,q,obs)
        assert fit['selected']==max(range(5),key=lambda j:fit['random'][j]['trace'][-1]['objective']);assert [r['seed'] for r in fit['random']]==list(SEEDS)
        for j,trial in enumerate([fit['warm']]+fit['random']):
            initial=np.array(trial['initial_component']);final=np.array(trial['final_component']);expected_initial=(1-WARM_MASS)*oldcomponent+WARM_MASS*prior['word'] if not j else np.random.default_rng(trial['seed']).gamma(2.,1.,size=enlarged.shape)*q[None,:]*enlarged;expected_initial/=expected_initial.sum(axis=1,keepdims=True);np.testing.assert_allclose(initial,expected_initial,atol=1e-15)
            for c in (initial,final):assert not c[~enlarged].any() and np.all(c[enlarged]>0);np.testing.assert_allclose(c.sum(axis=1),1)
            t=trial['trace'];assert min(np.diff([r['objective'] for r in t]))>=-1e-6;rows+=len(t);assert trial['converged']
            ll,gamma=forward_backward(chain,mixture(final,q,EPSILON),obs['sequences']);lp=supported_log_prior(final,prior,sharing);np.testing.assert_allclose([ll,lp,ll+lp],[t[-1][k] for k in ('log_likelihood','prior','objective')],atol=1e-8)
            pred=np.concatenate(gamma).argmax(axis=1);assert token_metrics(pred,gold,masks)==t[-1]['scores']
            if seed==3001 and rate==.5 and proposal['strategy']=='context' and proposal['k']==2:
                replay=fit_run(chain,obs,gold,masks,initial,prior,q,EPSILON,sharing);assert replay['converged']==trial['converged'] and len(replay['trace'])==len(t);np.testing.assert_allclose(replay['final_component'],final,atol=1e-10)
                for a,b in zip(replay['trace'],t):
                    np.testing.assert_allclose([a[k] for k in ('log_likelihood','prior','objective')],[b[k] for k in ('log_likelihood','prior','objective')],atol=1e-8);assert a['scores']==b['scores']
                replayed+=1
            checked+=1
        r=report['proposal'];originalcovered=support[gold,ids];regained=(~originalcovered)&enlarged[gold,ids]
        assert r['added_pairs']==int(newpairs.sum())==r['true_added_pairs']+r['false_added_pairs'];assert r['true_added_pairs']==int((newpairs&reference).sum());assert r['candidate_regained_query']==int((regained&query).sum())
        selected=fit['random'][fit['selected']];pred=predict(chain,selected['final_component'],q,obs);np.testing.assert_array_equal(pred[query],report['predicted_query']);delta=(pred==gold).astype(int)-(baseline==gold).astype(int)
        assert report['changes']['corrected_query']-report['changes']['spoiled_query']==report['changes']['net_query']==int(delta[query].sum());assert sum(report['sentence_delta'])==int(delta[query].sum())
        assert report['abstention']==abstention_metrics(pred[query],gold[query],~originalcovered[query],flagged[query])
    for summary in evaluation['summary']:
        group=[r for r in evaluation['cells'] if all(r[k]==summary[k] for k in ('arm','rate','strategy','k'))];assert summary['bootstrap']==bootstrap(group)
    for comparison in load(OUT/'comparisons.json'):
        ctx=sorted([r for r in evaluation['cells'] if r['arm']==comparison['arm'] and r['rate']==comparison['rate'] and r['k']==2 and r['strategy']=='context'],key=lambda r:r['mask_seed']);rnd=sorted([r for r in evaluation['cells'] if r['arm']==comparison['arm'] and r['rate']==comparison['rate'] and r['k']==2 and r['strategy']=='random'],key=lambda r:r['mask_seed']);diff=[dict(sentence_tokens=a['sentence_tokens'],sentence_delta=(np.array(a['sentence_delta'])-np.array(b['sentence_delta'])).tolist()) for a,b in zip(ctx,rnd)];assert comparison['bootstrap']==bootstrap(diff)
    result=dict(proposal_replays=constructed,final_fit_checks=checked,monotonic_objective_rows=rows,full_trajectory_replays=replayed,matched_random_caps=True,query_retrieval_and_error_counts=True,frozen_abstention_checked=True,bootstrap_replays=20,prior_hashes_valid=True,scope='Existing development only, oracle upstream context retained; reserved200 unscored')
    save(OUT/'validation.json',result);print(result)

if __name__=='__main__':run()
