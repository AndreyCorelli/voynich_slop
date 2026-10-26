"""Independent label/null-fit/prediction/metric and contrast replay."""
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_fixed_scaling_iteration184 import *

def run():
    hashes=fits=groups=0
    for name in ['design-freeze','omission-freeze','model-freeze','prediction-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    omissions=load(OUT/'omissions.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');selections=load(OUT/'selections.json');ranges=load(OUT/'ranges.json');paired=load(OUT/'paired.json');rescaled=load(ROOT/'iteration183/summary.json');skipped=load(OUT/'skipped.json');ff=load(ROOT/'iteration180/features.json');original=load(ROOT/'iteration180/source-labels.json');rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];target=[int(r['case_occurrence_pairs']>0) for r in rr]
    endpoints=sorted(set(r[k] for r in ff['earlier'] for k in ['a','b']));expected={'original':dict(endpoint=None,training=list(range(len(original))))}
    for i,w in enumerate(endpoints):expected['omit'+str(i)]=dict(endpoint=w,training=[j for j,r in enumerate(ff['earlier']) if r['a']!=w and r['b']!=w])
    assert expected==omissions==load(ROOT/'iteration183/omissions.json');labels={v:[original[i] for i in o['training']] for v,o in expected.items()};expected_skips={v:dict(training=len(y),positives=sum(y),reason='oneclass') for v,y in labels.items() if len(set(y))<2};assert skipped==expected_skips;assert set(models)==set(pred)==set(expected)-set(skipped)
    frozen=load(ROOT/'iteration180/models.json');oldpred=load(ROOT/'iteration180/predictions.json')['replication'];oldsummary=load(ROOT/'iteration180/summary.json')['replication'];allraw=np.array([r['values'] for r in ff['earlier']])
    for arm,cols in ARMS.items():
        assert models['original'][arm]==frozen[arm];assert pred['original'][arm]==oldpred[arm];assert summary['original'][arm]==oldsummary[arm]
        for view in models:
            yy=labels[view];raw=allraw[omissions[view]['training']][:,cols];full=allraw[:,cols];mean=full.mean(0);scale=full.std(0);scale[scale<1e-12]=1;x=np.column_stack([np.ones(len(raw)),(raw-mean)/scale]);penalty=np.eye(x.shape[1])*.1;penalty[0,0]=0;tx=np.column_stack([np.ones(len(rr)),(np.array([r['values'] for r in ff['replication']])[:,cols]-mean)/scale])
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
    expected_ranges={};control=summary['original']['frequency_support']['classification']['nll']
    for arm in ARMS:
        measures={}
        for view in summary:
            if view=='original':continue
            r=summary[view][arm];c=r['classification'];t=r['lists']['top10'];measures[view]=dict(nll=c['nll'],brier=c['brier'],auc=c['auc'],top10_applicability=t['edge_applicability'],top10_joint_yield=t['edge_joint_yield'],top10_case_types=t['case_types_involved'])
        expected_ranges[arm]={}
        for metric in ['nll','brier','auc','top10_applicability','top10_joint_yield','top10_case_types']:
            vals=[r[metric] for r in measures.values()];expected_ranges[arm][metric]=dict(n=len(vals),min=min(vals) if vals else None,max=max(vals) if vals else None,mean=sum(vals)/len(vals) if vals else None)
        overlaps=[len(set(selections['original'][arm]['top10'])&set(selections[v][arm]['top10'])) for v in measures];expected_ranges[arm]['baseline_top10_overlap']=dict(min=min(overlaps),max=max(overlaps));expected_ranges[arm]['nll_better_than_original_control']=sum(r['nll']<control for r in measures.values())
    expected_ranges['matched_rich_nll_better_than_control']=sum(s['rich']['classification']['nll']<s['frequency_support']['classification']['nll'] for v,s in summary.items() if v!='original');assert expected_ranges==ranges
    for view,arms in summary.items():
        if view=='original':continue
        for arm,record in arms.items():
            def extract(s):
                c=s['classification'];t=s['lists']['top10'];return dict(nll=c['nll'],brier=c['brier'],auc=c['auc'],top10_applicability=t['edge_applicability'],top10_joint_yield=t['edge_joint_yield'],top10_case_types=t['case_types_involved'])
            before=extract(rescaled[view][arm]);after=extract(record);assert paired[view][arm]=={m:dict(rescaled=before[m],fixed=after[m],fixed_minus_rescaled=after[m]-before[m]) for m in before}
    save(OUT/'audit.json',dict(frozen_hashes_verified=hashes,source_endpoint_omissions_verified=len(endpoints),distinct_training_masks=len({tuple(o['training']) for v,o in omissions.items() if v!='original'}),independent_newton_fits=fits,all_fixed_full_source_scaling_and_gradients_verified=True,selection_metric_groups=groups,all_predictions_classification_calibration_ranges_and_paired_contrasts=True,all180_original_models_predictions_and_summaries_exact=True))
    print('audit passed',fits,groups,flush=True)
if __name__=='__main__':run()
