"""Audit frozen inputs, replay EM objectives and independently count links."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_latent_classes_iteration26 import OUT,ARMS,SEEDS,load,save,digest,observe,arm_input,train_arm,decode,edges
from benchmarks.grammar_latent_classes_iteration26_evaluate import class_metrics
from voynich_smt.latent_cipher_classes import forward_backward,prior_data,log_prior


def run():
    for filename in ('fit-freeze.json','target-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p
    manifest=load(OUT/'manifest.json')
    for group in ('inputs','prior_declarations'):
        for p,h in manifest[group].items():assert digest(p)==h,p
    from benchmarks.grammar_latent_classes_iteration26 import RESERVE,strings
    reserved={r['sent_id'] for g in load(RESERVE)['authors'].values() for r in g}
    prior=set().union(*(set(strings(load(Path(p)))) for p in manifest['prior_declarations']))
    fresh=[sid for split,ids in manifest['split_ids'].items() if 'calibration' not in split for sid in ids]
    assert len(fresh)==len(set(fresh))==400 and not set(fresh)&(reserved|prior)
    data=load(OUT/'datasets.json');obs=load(OUT/'observations.json');models=load(OUT/'source-models.json');truth=load(OUT/'observation-truth.json');evaluation=load(OUT/'evaluation.json');predictions=load(OUT/'relation-predictions.json');policies=load(OUT/'policies.json')
    checked=0;replayed=0
    for split in ('calibration','jerome','caesar'):
        combined=data['background_'+split]+data[split]
        assert observe(combined)==observe(combined,26032)=={k:obs[split][k] for k in ('sequences','word_endings')}
        results=load(OUT/'calibration-fits.json') if split=='calibration' else load(OUT/'target-fits.json')[split]
        for arm,result in results.items():
            seq,we=arm_input(obs[split],arm);q,qe,within=prior_data(seq,we);chain=models['chains'][result['template']]
            assert [f['seed'] for f in result['fits']]==list(SEEDS)
            assert result['selected']==max(range(5),key=lambda i:result['fits'][i]['objective'])
            for f in result['fits']:
                e=np.array(f['emissions']);assert np.all(e>0);np.testing.assert_allclose(e.sum(axis=1),1)
                trace=f['trace'];assert min(np.diff([t['objective'] for t in trace]))>=-1e-6
                ll,_=forward_backward(chain,e,seq);obj=ll+log_prior(e,we,q,qe,within,arm in ('ending','shuffled_endings'))
                np.testing.assert_allclose([ll,obj],[trace[-1]['log_likelihood'],f['objective']],atol=1e-8);checked+=1
            # One full deterministic replay per arm and split, including all five starts.
            replay=train_arm(models,obs[split],arm);assert replay==result;replayed+=5
            if split!='calibration':
                gamma=decode(models,obs[split],result)
                assert class_metrics(gamma,truth[split][obs[split]['offset']:])['confusion']==evaluation[split][arm]['confusion']
                assert edges(gamma,models['relations'],policies[arm])==predictions[split][arm]
        if split=='calibration':continue
        for arm,rows in predictions[split].items():
            tp=pred=gold=0
            for row,s in zip(rows,data[split]):
                p={tuple(e[:3]) for e in row};g=set(map(tuple,s['edges']));tp+=len(p&g);pred+=len(p);gold+=len(g)
                heads={e[0]:e[1] for e in row};assert len(heads)==len(row)
                for c in heads:
                    seen=set();h=c
                    while h in heads:assert h not in seen;seen.add(h);h=heads[h]
            m=evaluation[split][arm]['relations']['micro'];np.testing.assert_allclose(m['f1'],2*tp/max(1,pred+gold));np.testing.assert_allclose(m['recall'],tp/max(1,gold))
            if pred:np.testing.assert_allclose(m['precision'],tp/pred)
    continuation=load(OUT/'development-continuation.json')['arms']
    for arm,r in continuation.items():
        f=r['continuation'];assert f['converged']
        assert min(np.diff([t['objective'] for t in f['trace']]))>=-1e-6
        seq,we=arm_input(obs['calibration'],arm);q,qe,within=prior_data(seq,we)
        ll,gamma=forward_backward(models['chains']['pooled'],f['emissions'],seq)
        np.testing.assert_allclose(ll+log_prior(f['emissions'],we,q,qe,within,arm=='ending'),f['objective'])
        score=class_metrics(gamma[obs['calibration']['offset']:],truth['calibration'][obs['calibration']['offset']:])
        assert score==r['after']
    report=dict(objective_checks=checked,deterministic_fit_replays=replayed,development_continuations_checked=2,fresh_sentences=400,reserved_unscored=200,rekey_invariant=True,input_hashes_valid=True,independent_link_counts=True)
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
