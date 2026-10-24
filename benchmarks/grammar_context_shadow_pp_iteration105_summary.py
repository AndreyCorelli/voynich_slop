"""Summarize fixed-position PP effects, preserving gross losses and wrong repairs."""
from benchmarks.grammar_context_shadow_pp_iteration105 import *


def run():
    evaluation=load(OUT/'evaluation.json');bank=load(ROOT/'iteration98/calibration-bank.json');summary={};comparisons=[]
    for view in ['base','civil','expanded']:
        for arm in ['frozen95','gain_gap','stability','lower','gain']:
            rows=[r[arm] for key,r in evaluation.items() if key.startswith(view+'/') and key.split('/')[1].startswith('swap_')];result=dict(cases=len(rows),pair_correct=sum(r['pair']['hit'] for r in rows),pair_wrong=sum(r['pair']['wrong'] for r in rows),controls_changed=sum(r[arm]['changed_tokens']>0 for key,r in evaluation.items() if key.startswith(view+'/') and not key.split('/')[1].startswith('swap_')),pp={})
            for model,cuts in PP_SETTINGS.items():
                for policy in cuts:
                    metrics=[r['pp'][model][policy] for r in rows];totals={phase:{k:sum(m[phase][k] for m in metrics) for k in ['tp','fp','fn','tn']} for phase in ['before','after','clean']}
                    for counts0 in totals.values():counts0['precision']=counts0['tp']/(counts0['tp']+counts0['fp']) if counts0['tp']+counts0['fp'] else None
                    result['pp'][model+'/'+policy]=dict(totals=totals,gross_changes={k:sum(m['changes'][k] for m in metrics) for k in ['new_tp','new_fp','lost_tp','removed_fp']},cases_matching_clean_probabilities=sum(m['maximum_probability_difference_from_clean']<=1e-12 for m in metrics),total_decision_differences_from_clean=sum(m['different_from_clean'] for m in metrics))
            summary[view+'/'+arm]=result
    for case in [k for k in bank if k.startswith('swap_')]:
        if 'base/'+case not in evaluation:continue
        b=evaluation['base/'+case]['frozen95'];a=evaluation['expanded/'+case]['frozen95']
        if a['pair']['hit'] and not b['pair']['hit']:
            comparisons.append(dict(case=case,base_pair=b['pair'],expanded_pair=a['pair'],original80_base_after=b['pp']['original']['fixed80']['after'],original80_expanded_after=a['pp']['original']['fixed80']['after'],base_vs_corrupt_gross=b['pp']['original']['fixed80']['changes'],expanded_vs_corrupt_gross=a['pp']['original']['fixed80']['changes']))
    wrong=[dict(case=key,arm=arm,pair=r['pair'],pp=r['pp']) for key,arms in evaluation.items() for arm,r in arms.items() if r['pair']['wrong']]
    save(OUT/'diagnostic-summary.json',dict(groups=summary,additional_exact_repairs_primary=comparisons,all_wrong_actions=wrong,limits='Sums repeat same1514tokenpositions across15syntheticerrorcases, NOTunique restored tokens or independent samples. No lexical/nuclei/Case/governor claims.'))
    audit_summary()
    print(json.dumps({k:v for k,v in summary.items() if k.endswith('/frozen95') or k.endswith('/gain_gap')},indent=2));print('ADDITIONAL',json.dumps(comparisons));print('WRONGACTIONS',[(r['case'],r['arm']) for r in wrong])
def audit_summary():
    evaluation=load(OUT/'evaluation.json');summary=load(OUT/'diagnostic-summary.json');checks=0
    for key,group in summary['groups'].items():
        view,arm=key.split('/');rows=[v[arm] for k,v in evaluation.items() if k.startswith(view+'/') and k.split('/')[1].startswith('swap_')]
        for setting,s in group['pp'].items():
            model,policy=setting.split('/');metrics=[r['pp'][model][policy] for r in rows]
            for phase in ['before','after','clean']:
                for k in ['tp','fp','fn','tn']:assert s['totals'][phase][k]==sum(m[phase][k] for m in metrics);checks+=1
            for k in ['new_tp','new_fp','lost_tp','removed_fp']:assert s['gross_changes'][k]==sum(m['changes'][k] for m in metrics);checks+=1
            assert s['totals']['after']['tp']-s['totals']['before']['tp']==s['gross_changes']['new_tp']-s['gross_changes']['lost_tp']
            assert s['totals']['after']['fp']-s['totals']['before']['fp']==s['gross_changes']['new_fp']-s['gross_changes']['removed_fp']
    assert len(summary['additional_exact_repairs_primary'])==5
    save(OUT/'summary-audit.json',dict(aggregate_count_fields_recomputed=checks,five_additional_exact_repairs_verified=True,net_gross_identities_verified=True))


if __name__=='__main__':run()
