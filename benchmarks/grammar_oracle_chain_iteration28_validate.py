"""Independent oracle-chain counts and full trajectory replay."""
import numpy as np
from benchmarks.grammar_oracle_chain_iteration28 import OUT,BASELINE,PREVIOUS,MAX_ITER,TOL,load,save,digest
from benchmarks.grammar_oracle_emission_challenge_iteration27 import score
from benchmarks.grammar_oracle_chain_iteration28_evaluate import summarize
from voynich_smt.latent_cipher_classes import fit,forward_backward,oracle_emissions
from voynich_smt.oracle_emission_challenge import decomposition,changed_tokens,em_step


def run():
    for filename in (OUT/'manifest.json',PREVIOUS/'verification-manifest.json',BASELINE/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'chains.json')==load(OUT/'manifest.json')['chains_hash']
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chains=load(OUT/'chains.json');chain=chains['oracle_development'];results=load(OUT/'results.json');old=load(BASELINE/'results.json');analysis=load(OUT/'analysis.json')
    # Independent counting, including stop in the transition-row denominator.
    start=np.full(8,.5);trans=np.full((8,8),.5);stop=np.full(8,.5);occupancy=np.zeros(8)
    for y in truth:
        start[y[0]]+=1;stop[y[-1]]+=1
        for s in y:occupancy[s]+=1
        for a,b in zip(y,y[1:]):trans[a,b]+=1
    np.testing.assert_allclose(chain['start'],start/start.sum());den=trans.sum(axis=1)+stop
    np.testing.assert_allclose(chain['transition'],trans/den[:,None]);np.testing.assert_allclose(chain['stop'],stop/den)
    np.testing.assert_allclose(chain['source_occupancy'],occupancy/occupancy.sum())
    assert chains['source']==load(PREVIOUS/'source-models.json')['chains']['pooled'];assert chains['source']!=chain
    checked=rows=0
    data=load(PREVIOUS/'datasets.json');records=data['background_calibration']+data['calibration']
    for arm,r in results.items():
        sharing=arm=='ending';oracle=r['oracle']
        np.testing.assert_allclose(oracle['initial_emissions'],old[arm]['oracle']['initial_emissions'],atol=1e-15)
        np.testing.assert_allclose(oracle['initial_emissions'],oracle_emissions(chain,obs['sequences'],obs['word_endings'],truth,sharing))
        for i,trial in enumerate([oracle]+r['random']):
            if i:
                previous=old[arm]['random'][i-1];assert trial['seed']==previous['seed'];np.testing.assert_allclose(trial['initial_emissions'],previous['initial_emissions'],atol=1e-15)
            replay=fit(chain,obs['sequences'],obs['word_endings'],trial.get('seed',0),sharing,max_iter=MAX_ITER,tolerance=TOL,initial=trial['initial_emissions'])
            assert replay['converged']==trial['converged'];assert len(replay['trace'])==len(trial['trace'])
            np.testing.assert_allclose(replay['emissions'],trial['final_emissions'],atol=1e-10)
            for a,b in zip(replay['trace'],trial['trace']):
                np.testing.assert_allclose([a['objective'],a['log_likelihood']],[b['objective'],b['log_likelihood']],atol=1e-8);rows+=1
            assert min(np.diff([t['objective'] for t in trial['trace']]))>=-1e-6
            for i,name in ((0,'initial_emissions'),(-1,'final_emissions')):
                _,gamma=forward_backward(chain,trial[name],obs['sequences']);assert score(gamma,truth)==trial['trace'][i]['all'];assert score(gamma[obs['offset']:],truth[obs['offset']:])==trial['trace'][i]['query']
            checked+=1
        first=oracle['first_corruption'];assert first['iteration']==oracle['first_net_accuracy_loss']['iteration']==1
        a=np.array(first['before_emissions']);b=np.array(first['after_emissions']);np.testing.assert_allclose(a,oracle['initial_emissions']);np.testing.assert_allclose(b,em_step(chain,a,obs['sequences'],obs['word_endings'],sharing))
        ll,ga=forward_backward(chain,a,obs['sequences']);nl,gb=forward_backward(chain,b,obs['sequences']);assert first['changes']==changed_tokens(ga,gb,truth,obs['sequences'],obs['offset'])
        for e,likelihood in ((a,ll),(b,nl)):
            d=decomposition(chain,e,obs['sequences']);np.testing.assert_allclose(d['log_likelihood'],likelihood,atol=1e-8)
            np.testing.assert_allclose(sum(d[k] for k in ('start','transition','stop','emission','posterior_entropy')),likelihood,atol=1e-8)
        assert first['delta']['log_likelihood']>0 and first['delta']['objective']>0
        for name,path in [('oracle_development',OUT),('source',BASELINE)]:
            assert summarize(load(path/'results.json')[arm],chains[name],obs,truth,records)==analysis[name][arm]
    report=dict(full_trajectory_replays=checked,objective_trace_entries=rows,independent_oracle_chain_counts=True,identical_emission_initializations=True,first_corruption_audits=2,prior_hashes_valid=True,scope='Previously inspected development only; no new target scoring; reserve200 unscored')
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
