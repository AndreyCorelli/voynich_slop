"""Replay every trajectory; independently verify first-loss decomposition."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_oracle_emission_challenge_iteration27 import OUT,PREVIOUS,MAX_ITER,TOL,load,save,digest,score
from voynich_smt.latent_cipher_classes import fit,forward_backward,oracle_emissions,prior_data,log_prior
from voynich_smt.oracle_emission_challenge import decomposition,changed_tokens,em_step


def run():
    for manifest in (OUT/'manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(manifest)['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chain=load(PREVIOUS/'source-models.json')['chains']['pooled'];results=load(OUT/'results.json');analysis=load(OUT/'analysis.json');q,qe,within=prior_data(obs['sequences'],obs['word_endings']);checked=0;rows=0
    for arm,r in results.items():
        sharing=arm=='ending';oracle=r['oracle'];expected=oracle_emissions(chain,obs['sequences'],obs['word_endings'],truth,sharing)
        np.testing.assert_allclose(oracle['initial_emissions'],expected)
        for run in [oracle]+r['random']:
            replay=fit(chain,obs['sequences'],obs['word_endings'],run.get('seed',0),sharing,max_iter=MAX_ITER,tolerance=TOL,initial=run['initial_emissions'])
            assert replay['converged']==run['converged'];assert len(replay['trace'])==len(run['trace'])
            np.testing.assert_allclose(replay['emissions'],run['final_emissions'],atol=1e-10)
            for a,b in zip(replay['trace'],run['trace']):
                np.testing.assert_allclose([a['objective'],a['log_likelihood']],[b['objective'],b['log_likelihood']],atol=1e-8);rows+=1
            for index in (0,-1):
                e=run['initial_emissions'] if index==0 else run['final_emissions'];_,g=forward_backward(chain,e,obs['sequences'])
                assert score(g,truth)==run['trace'][index]['all']
                assert score(g[obs['offset']:],truth[obs['offset']:])==run['trace'][index]['query']
            checked+=1
        first=oracle['first_corruption'];assert first['iteration']==oracle['first_net_accuracy_loss']['iteration']==1
        a=np.array(first['before_emissions']);b=np.array(first['after_emissions']);np.testing.assert_allclose(a,oracle['initial_emissions'])
        np.testing.assert_allclose(b,em_step(chain,a,obs['sequences'],obs['word_endings'],sharing))
        ll,ga=forward_backward(chain,a,obs['sequences']);nl,gb=forward_backward(chain,b,obs['sequences'])
        assert changed_tokens(ga,gb,truth,obs['sequences'],obs['offset'])==first['changes']
        for name,e,likelihood in [('before',a,ll),('after',b,nl)]:
            parts=decomposition(chain,e,obs['sequences']);np.testing.assert_allclose(parts['log_likelihood'],likelihood,atol=1e-8)
            np.testing.assert_allclose(sum(parts[k] for k in ('start','transition','stop','emission','posterior_entropy')),likelihood,atol=1e-8)
        assert first['delta']['objective']>0 and first['delta']['log_likelihood']>0
        assert first['posterior_kl_old_to_new']>=0
        # With fixed posterior, complete-label MAP was already optimized by oracle init.
        assert analysis[arm]['gold_path_plus_prior_delta']<0
    save(OUT/'validation.json',dict(full_trajectory_replays=checked,objective_trace_entries=rows,first_update_audits=2,all_prior_hashes_valid=True,
        scope='Only already inspected development240 sentences; no new target or reserved reads'))
    print('Validated',checked,'full trajectories;',rows,'trace entries and both first-corruption audits')

if __name__=='__main__':run()
