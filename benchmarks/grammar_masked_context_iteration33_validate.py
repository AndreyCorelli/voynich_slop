"""Independent per-target masking checks against original HMM inference."""
import numpy as np
from benchmarks.grammar_masked_context_iteration33 import OUT,FITS,HARD,BASELINE,EXACT,PREVIOUS,RATES,EPSILONS,PRIMARY,MASK_SEEDS,load,save,digest
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture
from voynich_smt.missing_class_support import missing_support,cohorts


def run():
    for filename in (OUT/'manifest.json',FITS/'verification-manifest.json',HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);evaluations=load(OUT/'evaluation.json');t=np.array(chain['transition']);start=np.array(chain['start']);stop=np.array(chain['stop']);masks_checked=rows=metric_checks=0;oracle_cache=None
    for row,filename in zip(evaluations,load(OUT/'probe-index.json')):
        seed=row['mask_seed'];rate=row['rate'];eps=row['epsilon'];arm=row['arm'];prediction=load(OUT/filename);support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset']);fit=load(FITS/f'fits-{seed}-{rate}-{eps}-{arm}.json');selected=fit['random'][fit['selected']];emission=mixture(selected['final_component'],q,eps)
        assert selected['seed']==row['selected_seed'];ordinary=forward_backward(chain,emission,obs['sequences'])[1];offset=0
        oracle=np.array(prediction['probabilities']['oracle_context'])
        if oracle_cache is None:oracle_cache=oracle
        else:np.testing.assert_array_equal(oracle,oracle_cache)
        for sent_index,(seq,y,gamma) in enumerate(zip(obs['sequences'],truth,ordinary)):
            n=len(seq);chosen=(sent_index+seed)%n
            # Alternate implementation: explicitly replace one target's evidence
            # with ones, then run the original batched forward-backward routine.
            evidence=emission[:,seq].copy();evidence[:,chosen]=1.
            _,masked=forward_backward(chain,evidence,[list(range(n))]);masked=masked[0];item=prediction['tokens'][offset+chosen]
            np.testing.assert_allclose(masked[chosen],prediction['probabilities']['masked_hmm'][offset+chosen],atol=1e-12)
            assert item['left_inferred']==(int(masked[chosen-1].argmax()) if chosen else None)
            assert item['right_inferred']==(int(masked[chosen+1].argmax()) if chosen+1<n else None);masks_checked+=1
            for i,s in enumerate(y):
                index=offset+i;record=prediction['tokens'][index];assert record['gold']==s and record['word_id']==seq[i]
                a=start if not i else t[y[i-1]];b=stop if i+1==n else t[:,y[i+1]];v=a*b;v/=v.sum();np.testing.assert_allclose(v,oracle[index],atol=1e-12)
                joint=v*emission[:,seq[i]];joint/=joint.sum();np.testing.assert_allclose(joint,prediction['probabilities']['oracle_context_with_emission'][index],atol=1e-12)
                a=start if record['left_inferred'] is None else t[record['left_inferred']];b=stop if record['right_inferred'] is None else t[:,record['right_inferred']];p=a*b;p/=p.sum();np.testing.assert_allclose(p,prediction['probabilities']['masked_neighbors'][index],atol=1e-12)
                if record['neighbors_correct']:np.testing.assert_allclose(p,v,atol=1e-12)
                rows+=1
            np.testing.assert_allclose(gamma,prediction['probabilities']['ordinary_hmm'][offset:offset+n],atol=1e-12);offset+=n
        for mode,pp in prediction['probabilities'].items():
            pp=np.array(pp);np.testing.assert_allclose(pp.sum(axis=1),1);assert np.all(np.isfinite(pp)) and np.all(pp>=0)
            order=np.argsort(-pp,axis=1,kind='stable');pred=order[:,0]
            for name,m in masks.items():
                r=row['metrics'][mode][name];assert r['tokens']==int(m.sum())
                if m.any():
                    np.testing.assert_allclose(r['accuracy'],(pred[m]==gold[m]).mean());np.testing.assert_allclose(r['top2'],np.any(order[m,:2]==gold[m,None],axis=1).mean());np.testing.assert_allclose(r['top3'],np.any(order[m,:3]==gold[m,None],axis=1).mean());assert sum(map(sum,r['confusion']))==int(m.sum())
                metric_checks+=1
        correct=np.array([r['neighbors_correct'] for r in prediction['tokens']])
        for name,audit in row['neighbor_audit'].items():assert audit['neighbors_correct']==int((masks[name]&correct).sum())
    report=dict(probes=len(evaluations),token_probability_rows=rows,independent_target_mask_replays=masks_checked,independent_cohort_metric_checks=metric_checks,oracle_context_invariant=True,correct_neighbor_predictions_match_oracle=True,prior_hashes_valid=True,scope='Existing development only; no new fits or reserved scoring')
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
