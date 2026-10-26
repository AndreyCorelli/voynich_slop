"""Independent trial inventory, weighted Newton, frozen-mask and effect audit."""
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_positive_addback_iteration191 import *

def run():
    hashes=fits=groups=0
    for name in ['design-freeze','trial-freeze','model-freeze','prediction-freeze','selection-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    ff=load(ROOT/'iteration180/features.json');y=load(ROOT/'iteration180/source-labels.json');om=load(ROOT/'iteration188/omissions.json');weak=load(ROOT/'iteration189/cohorts.json')['weak_le7'];trials=load(OUT/'trials.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');sel=load(OUT/'selections.json');summary=load(OUT/'summary.json');effects=load(OUT/'effects.json');permask=load(OUT/'per-mask.json');perexample=load(OUT/'per-example.json');masks=load(ROOT/'iteration188/accepted-masks.json');reference=load(ROOT/'iteration180/models.json');base_models=load(ROOT/'iteration190-retry/models.json');base_pred=load(ROOT/'iteration190-retry/predictions.json');base_summary=load(ROOT/'iteration190-retry/summary.json');rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];target=[int(r['case_occurrence_pairs']>0) for r in rr];expected={};verified={}
    for mask in weak:
        ix=om[mask]['training'];expected[mask+'/base']=dict(mask=mask,addback=None,training=ix)
        for i in range(52):
            if y[i]==1 and i not in ix:expected[mask+'/add'+str(i)]=dict(mask=mask,addback=i,training=sorted(ix+[i]))
    assert trials==expected
    for view,t in trials.items():
        ix=t['training'];yy=np.array([y[i] for i in ix]);mass=np.array([(18/52)/sum(yy==1) if label else (34/52)/sum(yy==0) for label in yy]);key=tuple(ix)
        if key in verified:assert models[view]==verified[key]
        else:
            for arm,cols in ARMS.items():
                ref=reference[arm];m=models[view][arm];assert m['columns']==cols and m['mean']==ref['mean'] and m['scale']==ref['scale'] and m['strength']==.1;x=np.column_stack([np.ones(len(ix)),(np.array([ff['earlier'][i]['values'] for i in ix])[:,cols]-m['mean'])/m['scale']]);pen=np.eye(x.shape[1])*.1;pen[0,0]=0;beta=np.zeros(x.shape[1])
                for _ in range(100):
                    p=expit(x@beta);g=x.T@(mass*(p-yy))+pen@beta;h=(x.T*(mass*p*(1-p)))@x+pen;delta=np.linalg.solve(h,g);beta-=delta
                    if max(abs(delta))<1e-12:break
                frozen=np.array(m['beta']);assert max(abs(beta-frozen))<1e-5;g=x.T@(mass*(expit(x@frozen)-yy))+pen@frozen;assert max(abs(g))<1e-6;close(m['gradient_max'],float(max(abs(g))));close(m['objective'],float(mass@(np.logaddexp(0,x@frozen)-yy*(x@frozen))+.5*frozen@pen@frozen));fits+=1
            verified[key]=models[view]
        if t['addback'] is None:assert models[view]==base_models[t['mask']] and pred[view]==base_pred[t['mask']]
        for arm,m in models[view].items():
            tx=np.column_stack([np.ones(126),(np.array([r['values'] for r in ff['replication']])[:,m['columns']]-m['mean'])/m['scale']]);close(pred[view][arm],expit(tx@np.array(m['beta'])).tolist());pp=pred[view][arm]
            for policy,accepted in masks[t['mask']].items():
                global_lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
                for k in [10,20]:
                    cutoff=sorted(pp,reverse=True)[min(k,len(pp))-1];global_lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cutoff]
                lists={'trim_'+label:[i for i in ix if i in accepted] for label,ix in global_lists.items()}
                for k in [10,20]:
                    cutoff=sorted([pp[i] for i in accepted],reverse=True)[min(k,len(accepted))-1] if accepted else None;lists['refill_top'+str(k)]=[i for i in accepted if cutoff is not None and pp[i]>=cutoff]
                assert lists==sel[view][policy][arm];s=summary[view][policy][arm];close(s['classification'],independent_evaluate([target[i] for i in accepted],[pp[i] for i in accepted]) if accepted else None)
                for label,ix in lists.items():close(s['lists'][label],independent_metrics([rr[i] for i in ix],857));groups+=1
                if t['addback'] is None:assert s['classification']==base_summary[t['mask']][policy]['arms'][arm]['accepted_classification'] and s['lists']==base_summary[t['mask']][policy]['arms'][arm]['lists']
    for view,arms in effects.items():
        t=trials[view];before=summary[t['mask']+'/base'];after=summary[view]
        for arm,r in arms.items():
            b=before['left_entropy'][arm]['lists']['refill_top10'];a=after['left_entropy'][arm]['lists']['refill_top10'];assert r==dict(base_case_pairs=b['case_edges'],after_case_pairs=a['case_edges'],change=a['case_edges']-b['case_edges'],base_joint=b['edge_joint_yield'],after_joint=a['edge_joint_yield'],base_nll=before['none'][arm]['classification']['nll'],after_nll=after['none'][arm]['classification']['nll'])
    for mask,s in permask.items():
        rows=[effects[v]['rich'] for v,t in trials.items() if t['mask']==mask and t['addback'] is not None];assert s==dict(trials=len(rows),baseline=summary[mask+'/base']['left_entropy']['rich']['lists']['refill_top10']['case_edges'],min_applicable=min(r['after_case_pairs'] for r in rows),max_applicable=max(r['after_case_pairs'] for r in rows),improved=sum(r['change']>0 for r in rows),worsened=sum(r['change']<0 for r in rows),unchanged=sum(r['change']==0 for r in rows))
    for i,s in perexample.items():
        views=[v for v,t in trials.items() if t['addback']==int(i)];changes=[effects[v]['rich']['change'] for v in views];assert s==dict(trials=len(views),distinct_base_masks=len({tuple(om[trials[v]['mask']]['training']) for v in views}),improved=sum(c>0 for c in changes),worsened=sum(c<0 for c in changes),unchanged=sum(c==0 for c in changes),min_change=min(changes),max_change=max(changes),mean_change=sum(changes)/len(changes))
    common=set(om[weak[0]]['endpoints'])
    for v in weak:common&=set(om[v]['endpoints'])
    incident=[i for i,r in enumerate(ff['earlier']) if common&{r['a'],r['b']}]
    save(OUT/'audit.json',dict(frozen_hashes_verified=hashes,weak_masks_verified=len(weak),single_positive_addback_trials_verified=len(effects),unique_training_masks=len(verified),independent_newton_fits=fits,all_class_mass_and_base_acceptance_masks_fixed=True,all_predictions_and_selection_metric_groups=groups,all190_baselines_exact=True,all_per_mask_and_example_effects=True,common_omitted_endpoint_ids=sorted(common),common_endpoint_incident_positive_rows=[i for i in incident if y[i]],common_endpoint_incident_negative_rows=[i for i in incident if not y[i]]))
    print('audit passed',fits,groups,flush=True)
if __name__=='__main__':run()
