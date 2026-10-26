"""Independent retained-range masks, lists, coverage and summary replay."""
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_class_mass_iteration190_retry import *

def run():
    hashes=groups=0
    for name in ['design-freeze','omission-freeze','mask-freeze','model-freeze','prediction-freeze','selection-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    ff=load(ROOT/'iteration180/features.json');omissions=load(OUT/'omissions.json');pred=load(OUT/'predictions.json');models=load(OUT/'models.json');skipped=load(OUT/'skipped.json');reference=load(ROOT/'iteration180/models.json');labels_source=load(ROOT/'iteration180/source-labels.json');oldsel={};oldsummary=load(ROOT/'iteration180/summary.json')['replication'];masks=load(OUT/'accepted-masks.json');mass_comparison=load(OUT/'mass-comparison.json');before_mass=load(ROOT/'iteration188/summary.json');sel=load(OUT/'selections.json');summary=load(OUT/'summary.json');ranges=load(OUT/'ranges.json');paired=load(OUT/'paired.json');truth=load(ROOT/'iteration172/details.json')['replication']['original']['all'];labels=[int(r['case_occurrence_pairs']>0) for r in truth]
    endpoints=sorted(set(r[k] for r in ff['earlier'] for k in ['a','b']));expected={'original':dict(endpoints=[],training=list(range(52)))}
    for k,(a,b) in enumerate(combinations(endpoints,2)):expected['omit'+str(k)]=dict(endpoints=[a,b],training=[i for i,r in enumerate(ff['earlier']) if not ({r['a'],r['b']}&{a,b})])
    assert expected==omissions==load(ROOT/'iteration188/omissions.json');assert masks==load(ROOT/'iteration188/accepted-masks.json');expected_skips={v:dict(training=len(o['training']),positives=sum(labels_source[i] for i in o['training']),reason='zero_or_oneclass') for v,o in omissions.items() if len(set(labels_source[i] for i in o['training']))<2};assert skipped==expected_skips;assert set(models)==set(pred)==set(omissions)-set(skipped);verified={};fits=0
    for view,arms in models.items():
        ix=omissions[view]['training'];yy=np.array([labels_source[i] for i in ix]);weights=np.array([(18/52)/sum(yy==1) if label else (34/52)/sum(yy==0) for label in yy]);assert math.isclose(sum(weights[yy==1]),18/52) and math.isclose(sum(weights[yy==0]),34/52);key=tuple(ix)
        if key in verified:assert arms==verified[key]
        else:
            for arm,cols in ARMS.items():
                m=arms[arm];ref=reference[arm];assert m['columns']==cols and m['mean']==ref['mean'] and m['scale']==ref['scale'] and m['strength']==.1;raw=np.array([ff['earlier'][i]['values'] for i in ix])[:,cols];x=np.column_stack([np.ones(len(ix)),(raw-ref['mean'])/ref['scale']]);pen=np.eye(x.shape[1])*.1;pen[0,0]=0;beta=np.zeros(x.shape[1])
                for _ in range(100):
                    pp=expit(x@beta);g=x.T@(weights*(pp-yy))+pen@beta;h=(x.T*(weights*pp*(1-pp)))@x+pen;delta=np.linalg.solve(h,g);beta-=delta
                    if max(abs(delta))<1e-12:break
                frozen=np.array(m['beta']);assert max(abs(beta-frozen))<1e-5;g=x.T@(weights*(expit(x@frozen)-yy))+pen@frozen;assert max(abs(g))<1e-6;close(m['gradient_max'],float(max(abs(g))));close(m['objective'],float(weights@(np.logaddexp(0,x@frozen)-yy*(x@frozen))+.5*frozen@pen@frozen));fits+=1
            verified[key]=arms
        oldsel[view]={}
        for arm,m in arms.items():
            tx=np.column_stack([np.ones(126),(np.array([r['values'] for r in ff['replication']])[:,m['columns']]-m['mean'])/m['scale']]);close(pred[view][arm],expit(tx@np.array(m['beta'])).tolist());pp=pred[view][arm];oldsel[view][arm]={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cutoff=sorted(pp,reverse=True)[min(k,len(pp))-1];oldsel[view][arm]['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cutoff]
    assert models['original']=={a:reference[a] for a in ARMS}
    for view,o in omissions.items():
        low=[min(ff['earlier'][i]['values'][j] for i in o['training']) for j in range(19)];high=[max(ff['earlier'][i]['values'][j] for i in o['training']) for j in range(19)];expected={'none':list(range(126)),'all_coordinates':[],'left_entropy':[]}
        for i,r in enumerate(ff['replication']):
            outside=[r['values'][j]<low[j]-1e-12 or r['values'][j]>high[j]+1e-12 for j in range(19)]
            if not any(outside):expected['all_coordinates'].append(i)
            if not outside[4] and not outside[13]:expected['left_entropy'].append(i)
        assert expected==masks[view]
        if view not in pred:continue
        for policy,accepted in expected.items():
            rejected=[i for i in range(126) if i not in accepted];coverage=dict(total=126,accepted=len(accepted),rejected=len(rejected),acceptance=len(accepted)/126,applicable_accepted=sum(labels[i] for i in accepted),applicable_lost=sum(labels[i] for i in rejected),noncase_rejected=sum(not labels[i] for i in rejected));assert coverage==summary[view][policy]['coverage']
            for arm,pp in pred[view].items():
                lists={'trim_'+name:[i for i in ix if i in accepted] for name,ix in oldsel[view][arm].items()}
                order=sorted(accepted,key=lambda i:pp[i],reverse=True)
                for k in [10,20]:
                    cut=pp[order[min(k,len(order))-1]] if order else None;lists['refill_top'+str(k)]=[i for i in accepted if cut is not None and pp[i]>=cut]
                assert lists==sel[view][policy][arm];result=summary[view][policy]['arms'][arm];close(result['accepted_classification'],independent_evaluate([labels[i] for i in accepted],[pp[i] for i in accepted]) if accepted else None)
                for name,ix in lists.items():close(result['lists'][name],independent_metrics([truth[i] for i in ix],857));groups+=1
                if policy=='none' and view=='original':
                    assert result['accepted_classification']==oldsummary[arm]['classification']
                    for name in ['threshold','top10','top20']:assert result['lists']['trim_'+name]==oldsummary[arm]['lists'][name]
    reconstructed={}
    for policy in POLICIES:
        rows=[r[policy] for v,r in summary.items() if v!='original'];reconstructed[policy]={}
        for metric in ['accepted','applicable_lost','noncase_rejected']:
            values=[r['coverage'][metric] for r in rows];reconstructed[policy][metric]=dict(min=min(values),max=max(values),mean=sum(values)/len(values))
        for arm in ARMS:
            reconstructed[policy][arm]={}
            for label in ['trim_top10','refill_top10']:
                reconstructed[policy][arm][label]={}
                for metric in ['edges','case_edges','edge_applicability','edge_joint_yield','case_types_involved']:
                    values=[r['arms'][arm]['lists'][label][metric] for r in rows];defined=[v for v in values if v is not None];reconstructed[policy][arm][label][metric]=dict(min=min(defined) if defined else None,max=max(defined) if defined else None,mean=sum(defined)/len(defined) if defined else None,undefined=len(values)-len(defined))
    assert reconstructed==ranges
    for v,policies in paired.items():
        for policy,arms in policies.items():
            for arm,r in arms.items():
                before=summary[v]['none']['arms'][arm]['lists']['refill_top10'];after=summary[v][policy]['arms'][arm]['lists']['refill_top10'];assert r==dict(base_case_pairs=before['case_edges'],after_case_pairs=after['case_edges'],case_pair_change=after['case_edges']-before['case_edges'],base_joint_yield=before['edge_joint_yield'],after_joint_yield=after['edge_joint_yield'])
    for view,policies in mass_comparison.items():
        for policy,arms in policies.items():
            for arm,record in arms.items():
                before=before_mass[view][policy]['arms'][arm];after=summary[view][policy]['arms'][arm];assert record==dict(old_case_pairs=before['lists']['refill_top10']['case_edges'],new_case_pairs=after['lists']['refill_top10']['case_edges'],case_pair_change=after['lists']['refill_top10']['case_edges']-before['lists']['refill_top10']['case_edges'],old_joint=before['lists']['refill_top10']['edge_joint_yield'],new_joint=after['lists']['refill_top10']['edge_joint_yield'],old_accepted_nll=before['accepted_classification']['nll'],new_accepted_nll=after['accepted_classification']['nll'])
    for p,h in load(ROOT/'iteration190/failed-attempt-manifest.json')['inputs'].items():assert digest(p)==h
    save(OUT/'audit.json',dict(frozen_hashes_verified=hashes,retained_source_mask_views_verified=len(omissions),double_omissions_verified=len(omissions)-1,unique_training_masks=len(verified),independent_newton_fits=fits,policies_per_view=3,all_source_only_bounds_and_acceptance_masks=True,selection_metric_groups=groups,all_coverage_applicable_loss_and_accepted_calibration=True,all180_original_baselines_exact=True,all_ranges_and_paired_metrics=True,all_fixed_scale_and_original_class_mass_models_verified=True,all188_masks_and_mass_comparisons_verified=True,failed_unscored_attempt_preserved=True))
    print('audit passed',groups,flush=True)
if __name__=='__main__':run()
