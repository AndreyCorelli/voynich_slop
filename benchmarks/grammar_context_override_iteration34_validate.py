"""Verify split separation, signal purity, calibration replay, and query harm."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_context_override_iteration34 import OUT,PREVIOUS,PROBES,EXACT,BASELINE,HARD,GRID,RISK,EPSILONS,load,save,digest,slice_features
from benchmarks.grammar_context_override_iteration34_evaluate import bootstrap
from voynich_smt.context_override import signals,calibrate,apply,counts
from voynich_smt.missing_class_support import missing_support


def run():
    for filename in (OUT/'evaluation-freeze.json',OUT/'manifest.json',PROBES/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];data=load(PREVIOUS/'datasets.json');calids={s['sent_id'] for s in data['background_calibration']};queryids={s['sent_id'] for s in data['calibration']};assert len(calids)==200 and len(queryids)==40 and not calids&queryids
    offset=sum(map(len,obs['sequences'][:obs['offset']]));n=sum(map(len,obs['sequences']));calmask=np.arange(n)<offset;query=~calmask;assert offset==1579 and int(query.sum())==473
    features=load(OUT/'features.json');truth=load(OUT/'feature-truth.json');policies=load(OUT/'policies.json');evaluation=load(OUT/'evaluation.json');reference=np.asarray(load(EXACT/'support-truth.json')['support']);additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');ids=np.concatenate(obs['sequences']);checks=0
    for f,y,filename in zip(features,truth,load(PROBES/'probe-index.json')):
        p=load(PROBES/filename);support,_=missing_support(reference,additions[str(f['mask_seed'])],deletions[str(f['mask_seed'])],f['rate'])
        expected=signals(p['probabilities']['masked_hmm'],p['probabilities']['ordinary_hmm'],support,ids);assert f['features']==expected
        assert set(expected)=={'old','new','disagree','outside_top','confidence','ratio','outside_mass','conflict'}
        np.testing.assert_array_equal(y['excluded'],~support[np.asarray(y['gold']),ids]);checks+=1
    for arm in ('word','ending'):
        for epsilon in EPSILONS:
            records=[dict(features=slice_features(f['features'],calmask),gold=np.asarray(y['gold'])[calmask].tolist(),excluded=np.asarray(y['excluded'])[calmask].tolist()) for f,y in zip(features,truth) if f['arm']==arm and f['epsilon']==epsilon]
            for gate in ('outside','disagreement'):
                result=calibrate(records,GRID,RISK,gate);assert result==policies[f'{arm}/{epsilon}/{gate}']
                assert result['calibration']['spoiled_correct_covered']<=RISK*result['calibration']['correct_covered']
                assert result['policy']['enabled']==(result['calibration']['net_gain']>0)
    for row in evaluation['cells']:
        i=next(i for i,f in enumerate(features) if all(f[k]==row[k] for k in ('mask_seed','rate','epsilon','arm')));f=slice_features(features[i]['features'],query);y=np.asarray(truth[i]['gold'])[query];excluded=np.asarray(truth[i]['excluded'])[query];policy=policies[f"{row['arm']}/{row['epsilon']}/{row['gate']}"]['policy'];pred,selected=apply(f,policy)
        np.testing.assert_array_equal(pred,row['predicted']);np.testing.assert_array_equal(selected,row['selected']);assert counts(f,y,selected,excluded)==row['counts']
        a=np.asarray(f['old']);b=np.asarray(f['new']);corrected=int((selected&(a!=y)&(b==y)).sum());spoiled=int((selected&(a==y)&(b!=y)).sum());assert corrected-spoiled==row['counts']['net_gain']==int((pred==y).sum()-(a==y).sum())
        np.testing.assert_allclose(row['delta_accuracy'],(corrected-spoiled)/len(y));assert sum(row['sentence_delta'])==corrected-spoiled
    # Pairwise AUC oracle, independent of score sorting/rank implementation.
    for d in evaluation['detection']:
        i=next(i for i,f in enumerate(features) if all(f[k]==d[k] for k in ('mask_seed','rate','epsilon','arm')));f=slice_features(features[i]['features'],query);y=np.asarray(truth[i]['excluded'])[query]
        scores=dict(outside_mass=np.array(f['outside_mass']),conflict=np.array(f['conflict']),outside_top_confidence=np.array(f['confidence'])*np.array(f['outside_top']))
        for name,s in scores.items():
            pos=s[y,None];neg=s[~y][None,:];auc=float(np.mean((pos>neg)+.5*(pos==neg)));np.testing.assert_allclose(d['scores'][name]['auroc'],auc,atol=1e-12)
    for arm,ee in evaluation['summary'].items():
        for eps,rr in ee.items():
            for rate,ss in rr.items():
                for gate in ('outside','disagreement'):
                    rows=[r for r in evaluation['cells'] if r['arm']==arm and str(r['epsilon'])==eps and str(r['rate'])==rate and r['gate']==gate];assert ss[gate]['bootstrap']==bootstrap(rows)
    report=dict(feature_purity_checks=checks,calibration_policy_replays=8,query_decision_audits=len(evaluation['cells']),independent_auc_checks=len(evaluation['detection'])*3,split_ids_disjoint=True,calibration_sentences=200,query_sentences=40,query_label_threshold_tuning=False,cluster_bootstrap_replays=16,prior_hashes_valid=True,scope='Internal reused development split; upstream oracle/transductive information retained; reserved200 unscored')
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
