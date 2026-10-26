"""Independent retained-range masks, lists, coverage and summary replay."""
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_abstention_iteration187 import *

def run():
    hashes=groups=0
    for name in ['design-freeze','mask-freeze','selection-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    ff=load(ROOT/'iteration180/features.json');omissions=load(ROOT/'iteration184/omissions.json');pred=load(ROOT/'iteration184/predictions.json');oldsel=load(ROOT/'iteration184/selections.json');oldsummary=load(ROOT/'iteration184/summary.json');masks=load(OUT/'accepted-masks.json');sel=load(OUT/'selections.json');summary=load(OUT/'summary.json');ranges=load(OUT/'ranges.json');paired=load(OUT/'paired.json');truth=load(ROOT/'iteration172/details.json')['replication']['original']['all'];labels=[int(r['case_occurrence_pairs']>0) for r in truth]
    for view,o in omissions.items():
        low=[min(ff['earlier'][i]['values'][j] for i in o['training']) for j in range(19)];high=[max(ff['earlier'][i]['values'][j] for i in o['training']) for j in range(19)];expected={'none':list(range(126)),'all_coordinates':[],'left_entropy':[]}
        for i,r in enumerate(ff['replication']):
            outside=[r['values'][j]<low[j]-1e-12 or r['values'][j]>high[j]+1e-12 for j in range(19)]
            if not any(outside):expected['all_coordinates'].append(i)
            if not outside[4] and not outside[13]:expected['left_entropy'].append(i)
        assert expected==masks[view]
        for policy,accepted in expected.items():
            rejected=[i for i in range(126) if i not in accepted];coverage=dict(total=126,accepted=len(accepted),rejected=len(rejected),acceptance=len(accepted)/126,applicable_accepted=sum(labels[i] for i in accepted),applicable_lost=sum(labels[i] for i in rejected),noncase_rejected=sum(not labels[i] for i in rejected));assert coverage==summary[view][policy]['coverage']
            for arm,pp in pred[view].items():
                lists={'trim_'+name:[i for i in ix if i in accepted] for name,ix in oldsel[view][arm].items()}
                order=sorted(accepted,key=lambda i:pp[i],reverse=True)
                for k in [10,20]:
                    cut=pp[order[min(k,len(order))-1]] if order else None;lists['refill_top'+str(k)]=[i for i in accepted if cut is not None and pp[i]>=cut]
                assert lists==sel[view][policy][arm];result=summary[view][policy]['arms'][arm];close(result['accepted_classification'],independent_evaluate([labels[i] for i in accepted],[pp[i] for i in accepted]) if accepted else None)
                for name,ix in lists.items():close(result['lists'][name],independent_metrics([truth[i] for i in ix],857));groups+=1
                if policy=='none':
                    assert result['accepted_classification']==oldsummary[view][arm]['classification']
                    for name in ['threshold','top10','top20']:assert result['lists']['trim_'+name]==oldsummary[view][arm]['lists'][name]
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
    save(OUT/'audit.json',dict(frozen_hashes_verified=hashes,retained_source_mask_views_verified=54,policies_per_view=3,all_source_only_bounds_and_acceptance_masks=True,selection_metric_groups=groups,all_coverage_applicable_loss_and_accepted_calibration=True,all184_no_abstention_baselines_exact=True,all_ranges_and_paired_metrics=True,no_models_or_predictions_changed=True))
    print('audit passed',groups,flush=True)
if __name__=='__main__':run()
