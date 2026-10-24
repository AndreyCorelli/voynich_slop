"""Audit exact support and replay all constrained EM trajectories."""
import numpy as np
from benchmarks.grammar_supported_classes_iteration29 import OUT,BASELINE,PREVIOUS,load,save,digest,scores
from voynich_smt.latent_cipher_classes import forward_backward
from voynich_smt.supported_emissions import supported_prior,supported_update,supported_step,supported_log_prior
from voynich_smt.oracle_emission_challenge import changed_tokens


def run():
    for path in (OUT/'manifest.json',PREVIOUS/'verification-manifest.json',BASELINE/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'support-truth.json')==load(OUT/'manifest.json')['support_hash']
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chain=load(BASELINE/'chains.json')['oracle_development'];st=load(OUT/'support-truth.json');support=np.asarray(st['support']);counts=np.zeros_like(st['gold_counts'],dtype=float)
    for seq,y in zip(obs['sequences'],truth):
        for w,s in zip(seq,y):counts[s,w]+=1
    np.testing.assert_array_equal(counts,st['gold_counts']);np.testing.assert_array_equal(counts>0,support)
    prior=supported_prior(obs['sequences'],obs['word_endings'],support);np.testing.assert_allclose(prior['word'].sum(axis=1),1);np.testing.assert_allclose(prior['end'].sum(axis=1),1)
    assert not np.any(prior['word'][~support]);results=load(OUT/'results.json');analysis=load(OUT/'analysis.json');rows=0;checked=0;all_predictions=[]
    for arm,r in results.items():
        sharing=arm=='ending';np.testing.assert_allclose(r['oracle']['initial_emissions'],supported_update(counts,prior,sharing))
        for trial in [r['oracle']]+r['random']:
            assert trial['converged'];e=np.array(trial['initial_emissions']);old_objective=-np.inf
            for i,row in enumerate(trial['trace']):
                assert not np.any(e[~support]);np.testing.assert_allclose(e.sum(axis=1),1)
                ll,gamma=forward_backward(chain,e,obs['sequences']);lp=supported_log_prior(e,prior,sharing);np.testing.assert_allclose([ll,lp,ll+lp],[row['log_likelihood'],row['prior'],row['objective']],atol=1e-8)
                assert ll+lp>=old_objective-1e-6;old_objective=ll+lp
                assert scores(gamma,truth,obs['sequences'],support,obs['offset'])=={k:row[k] for k in ('all','query','ambiguous_all','ambiguous_query')}
                for seq,g,y in zip(obs['sequences'],gamma,truth):
                    pred=g.argmax(axis=1)
                    for w,p,reference in zip(seq,pred,y):
                        assert support[p,w]
                        if support[:,w].sum()==1:assert p==reference
                rows+=1
                if i+1<len(trial['trace']):e=supported_step(chain,e,obs['sequences'],prior,sharing)
            np.testing.assert_allclose(e,trial['final_emissions'],atol=1e-10);checked+=1;all_predictions.append(np.concatenate(gamma).argmax(axis=1))
        first=r['oracle']['first_corruption'];a=np.array(first['before_emissions']);b=np.array(first['after_emissions']);assert first['iteration']==1
        np.testing.assert_allclose(a,r['oracle']['initial_emissions']);np.testing.assert_allclose(b,supported_step(chain,a,obs['sequences'],prior,sharing))
        _,ga=forward_backward(chain,a,obs['sequences']);_,gb=forward_backward(chain,b,obs['sequences']);assert changed_tokens(ga,gb,truth,obs['sequences'],obs['offset'])==first['changes']
        f=analysis['arms'][arm]['first_corruption'];assert f['delta']['objective']>0 and f['delta']['log_likelihood']>0 and f['delta']['prior']<0
        assert f['posterior_kl_old_to_new']>=0
        for c in f['changes']:assert support[:,c['word_id']].sum()>1
        final=analysis['arms'][arm]['final'];np.testing.assert_allclose(final['query']['correct'],final['ambiguous_query']['correct']+final['query']['tokens']-final['ambiguous_query']['tokens'])
    same=all(np.array_equal(all_predictions[0],p) for p in all_predictions[1:]);assert same
    report=dict(full_trajectory_replays=checked,objective_and_accuracy_rows=rows,independent_gold_support_counts=True,forbidden_probability_checks='All iterates exact zero; singleton-support tags always reference-correct',
        all_twelve_final_token_predictions_identical=same,first_corruption_audits=2,prior_hashes_valid=True,scope='Existing development240 only; fresh targets and reserved200 unscored')
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
