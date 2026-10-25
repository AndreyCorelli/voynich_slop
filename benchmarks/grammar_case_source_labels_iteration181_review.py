"""Independent label/null-fit/prediction/metric and contrast replay."""
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_source_labels_iteration181 import *

def run():
    hashes=fits=groups=0
    for name in ['design-freeze','label-freeze','model-freeze','prediction-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    labels=load(OUT/'source-labels.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');selections=load(OUT/'selections.json');scalars=load(OUT/'scalar-scores.json');contrasts=load(OUT/'contrasts.json');ff=load(ROOT/'iteration180/features.json');original=load(ROOT/'iteration180/source-labels.json');rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];target=[int(r['case_occurrence_pairs']>0) for r in rr]
    assert labels['original']==original
    for seed in NULL_SEEDS:
        v='label'+str(seed);assert labels[v]==np.random.default_rng(seed).permutation(original).tolist();assert Counter(labels[v])==Counter(original)
    assert set(labels)==set(models)==set(pred)=={'original',*('label'+str(s) for s in NULL_SEEDS)}
    frozen=load(ROOT/'iteration180/models.json');oldpred=load(ROOT/'iteration180/predictions.json')['replication'];oldsummary=load(ROOT/'iteration180/summary.json')['replication']
    for arm,cols in ARMS.items():
        raw=np.array([r['values'] for r in ff['earlier']])[:,cols];mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1;x=np.column_stack([np.ones(len(raw)),(raw-mean)/scale]);penalty=np.eye(x.shape[1])*.1;penalty[0,0]=0;tx=np.column_stack([np.ones(len(rr)),(np.array([r['values'] for r in ff['replication']])[:,cols]-mean)/scale])
        assert models['original'][arm]==frozen[arm];assert pred['original'][arm]==oldpred[arm];assert summary['original'][arm]==oldsummary[arm]
        for view,yy in labels.items():
            y=np.array(yy);m=models[view][arm];assert m['columns']==cols and m['strength']==.1;close(m['mean'],mean.tolist());close(m['scale'],scale.tolist());beta=np.zeros(x.shape[1])
            for _ in range(100):
                p=expit(x@beta);gradient=x.T@(p-y)/len(y)+penalty@beta;hessian=(x.T*(p*(1-p)))@x/len(y)+penalty;delta=np.linalg.solve(hessian,gradient);beta-=delta
                if max(abs(delta))<1e-12:break
            frozen_beta=np.array(m['beta']);assert max(abs(beta-frozen_beta))<1e-5;gradient=x.T@(expit(x@frozen_beta)-y)/len(y)+penalty@frozen_beta;assert max(abs(gradient))<1e-6;close(m['gradient_max'],float(max(abs(gradient))));objective=float(np.mean(np.logaddexp(0,x@frozen_beta)-y*(x@frozen_beta))+.5*frozen_beta@penalty@frozen_beta);close(m['objective'],objective);pp=pred[view][arm];close(pp,expit(tx@frozen_beta).tolist());close(summary[view][arm]['classification'],independent_evaluate(target,pp));fits+=1
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cut=sorted(pp,reverse=True)[min(k,len(pp))-1];lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
            assert lists==selections[view][arm]
            for name,ix in lists.items():close(summary[view][arm]['lists'][name],independent_metrics([rr[i] for i in ix],857));groups+=1
            s=summary[view][arm];c=s['classification'];t=s['lists']['top10'];close(scalars[view][arm],dict(nll=c['nll'],brier=c['brier'],auc=c['auc'],top10_applicability=t['edge_applicability'],top10_joint_yield=t['edge_joint_yield'],top10_case_types=t['case_types_involved']))
    for v,s in scalars.items():close(s['rich_gain'],{m:(s['frequency_support'][m]-s['rich'][m] if m in ['nll','brier'] else s['rich'][m]-s['frequency_support'][m]) for m in s['rich']})
    for arm,mm in contrasts.items():
        for metric,r in mm.items():
            actual=scalars['original'][arm][metric];nn=[scalars['label'+str(seed)][arm][metric] for seed in NULL_SEEDS];lower=arm!='rich_gain' and metric in ['nll','brier'];tail=sum(x<=actual if lower else x>=actual for x in nn);assert r==dict(actual=actual,extreme='lower' if lower else 'higher',nulls=len(nn),mean=sum(nn)/len(nn),min=min(nn),max=max(nn),as_or_more_extreme=tail,descriptive_corrected_tail=(1+tail)/(1+len(nn)))
    save(OUT/'audit.json',dict(frozen_hashes_verified=hashes,source_label_permutations_verified=199,all_positive_counts_preserved=True,independent_newton_fits=fits,all_frozen_gradients_below_1e_minus6=True,selection_metric_groups=groups,all_predictions_and_classification_calibration_metrics=True,all180_original_models_predictions_and_summaries_exact=True,all_scalars_paired_gains_and_tail_directions=True))
    print('audit passed',fits,groups,flush=True)
if __name__=='__main__':run()
