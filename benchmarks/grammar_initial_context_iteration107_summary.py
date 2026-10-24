"""Initial-preserving full-bank comparison; all unavailable partners retained."""
from benchmarks.grammar_initial_context_iteration107 import *


def run():
    cases=load(OUT/'pair-cases.json');evaluation=load(OUT/'evaluation.json');actions=load(OUT/'actions.json');core=load(ROOT/'iteration100/core.json');bank=load(ROOT/'iteration98/calibration-bank.json');base={c['case']:c for c in cases if c['block']=='base'};summary={};wrong=[]
    for view in ['base','civil','expanded']:
        errors=[c for c in cases if c['block']==view and c['reference']['error']];controls=[c for c in cases if c['block']==view and not c['reference']['error']]
        strata={'all_errors':errors,'globally_present_errors':[c for c in errors if c['reference']['pair'] is not None],'scored_affected_errors':[c for c in errors if c['scored_affected_tokens']>0],'zero_affected_errors':[c for c in errors if not c['scored_affected_tokens']],'core_errors':[c for c in errors if set(bank[c['case']])<=set(core)],'original_supported_errors':[c for c in errors if base[c['case']]['reference']['supported']]}
        for arm in load(OUT/'policies.json'):
            group={}
            for name,selected_cases in strata.items():
                rows=[evaluation[view+'/'+c['case']][arm] for c in selected_cases];result=dict(cases=len(rows),pair_hit=sum(r['pair']['hit'] for r in rows),pair_wrong=sum(r['pair']['wrong'] for r in rows),pair_abstain=sum(r['pair']['abstain'] for r in rows),supported_true_pairs=sum(c['reference']['supported'] for c in selected_cases),raw_top1_correct=sum(c['features']['pair'] is not None and c['features']['pair']==c['reference']['pair'] for c in selected_cases),pp={})
                for model,cuts in PP_SETTINGS.items():
                    for policy in cuts:
                        ms=[r['pp'][model][policy] for r in rows];totals={phase:{k:sum(m[phase][k] for m in ms) for k in ['tp','fp','fn','tn']} for phase in ['before','after','clean']}
                        for t in totals.values():t.update(precision=t['tp']/(t['tp']+t['fp']) if t['tp']+t['fp'] else None,recall=t['tp']/(t['tp']+t['fn']) if t['tp']+t['fn'] else 0.)
                        result['pp'][model+'/'+policy]=dict(totals=totals,gross_changes={k:sum(m['changes'][k] for m in ms) for k in ['new_tp','new_fp','lost_tp','removed_fp']},matching_clean_probabilities=sum(m['maximum_probability_difference_from_clean']<=1e-12 for m in ms),decision_differences_from_clean=sum(m['different_from_clean'] for m in ms))
                group[name]=result
            group['controls']=[dict(case=c['case'],pair=evaluation[view+'/'+c['case']][arm]['pair'],pp=evaluation[view+'/'+c['case']][arm]['pp']) for c in controls];summary[view+'/'+arm]=group
    for c in cases:
        key=c['block']+'/'+c['case']
        for arm,r in evaluation[key].items():
            if r['pair']['wrong']:wrong.append(dict(case=key,arm=arm,selected_words=[c['identities'][i] for i in r['pair']['selected']],scored_affected_tokens=c['scored_affected_tokens'],reference_supported=c['reference']['supported'],features=c['features'],pp=r['pp']))
    # Matched 15-error comparison: only distractor pool changes from104/105.
    prior=load(ROOT/'iteration105/evaluation.json');distractions=[]
    for key,arms in prior.items():
        for arm in ['frozen95','gain_gap']:
            old=arms[arm];new=evaluation[key][arm]
            if old['pair']['hit']!=new['pair']['hit'] or old['pair']['wrong']!=new['pair']['wrong']:
                c=next(c for c in cases if c['block']+'/'+c['case']==key);distractions.append(dict(case=key,arm=arm,old_pair=old['pair'],new_pair=new['pair'],new_selected_words=[c['identities'][i] for i in new['pair']['selected']] if new['pair']['selected'] else None,old_pp=old['pp']['original']['fixed80'],new_pp=new['pp']['original']['fixed80']))
    previous=load(ROOT/'iteration106/evaluation.json');changes=[]
    for key,arms in evaluation.items():
        for arm in ['frozen95','gain_gap']:
            old=previous[key][arm];new=arms[arm]
            if old['pair']['hit']!=new['pair']['hit'] or old['pair']['wrong']!=new['pair']['wrong']:
                changes.append(dict(case=key,arm=arm,before_pair=old['pair'],after_pair=new['pair'],before_pp=old['pp']['original']['fixed80'],after_pp=new['pp']['original']['fixed80']))
    save(OUT/'diagnostic-summary.json',dict(tokenizer_outcome_changes=changes,groups=summary,all_wrong_actions=wrong,matched_core_distractions=distractions,limits='Alternative global synthetic mappings on same1514positions; sums NOTunique tokens/independent samples.2zeroaffectederrors separated;16candidates/195anchorssupplied; fixedmodel/cut, no lexical/nuclei/newannotation/reserve.'))
    audit_summary()
    for key,r in summary.items():
        if key.endswith('/frozen95') or key.endswith('/gain_gap'):
            print(key,'allerrors',r['all_errors']['pair_hit'],r['all_errors']['pair_wrong'],'affected',r['scored_affected_errors']['pair_hit'],r['scored_affected_errors']['pair_wrong'],'rawtop1',r['all_errors']['raw_top1_correct'],'supported',r['all_errors']['supported_true_pairs'],'controls',[(c['case'],c['pair']['wrong']) for c in r['controls']]);print('PPaffected',r['scored_affected_errors']['pp']['original/fixed80'])
    print('Wrongactions',len(wrong),'matchedcorechanges',len(distractions))
def audit_summary():
    evaluation=load(OUT/'evaluation.json');summary=load(OUT/'diagnostic-summary.json');cases=load(OUT/'pair-cases.json');bank=load(ROOT/'iteration98/calibration-bank.json');core=set(load(ROOT/'iteration100/core.json'));base={c['case']:c for c in cases if c['block']=='base'};checks=0
    for key,group in summary['groups'].items():
        view,arm=key.split('/')
        for stratum,result in group.items():
            if stratum=='controls':continue
            selected_cases=[c for c in cases if c['block']==view and c['reference']['error'] and (stratum!='globally_present_errors' or c['reference']['pair'] is not None) and (stratum!='scored_affected_errors' or c['scored_affected_tokens']>0) and (stratum!='zero_affected_errors' or not c['scored_affected_tokens']) and (stratum!='core_errors' or set(bank[c['case']])<=core) and (stratum!='original_supported_errors' or base[c['case']]['reference']['supported'])]
            rows=[evaluation[view+'/'+c['case']][arm] for c in selected_cases];assert len(rows)==result['cases']
            for setting,s in result['pp'].items():
                model,policy=setting.split('/');metrics=[r['pp'][model][policy] for r in rows]
                for phase in ['before','after','clean']:
                    for k in ['tp','fp','fn','tn']:assert s['totals'][phase][k]==sum(m[phase][k] for m in metrics);checks+=1
                for k in ['new_tp','new_fp','lost_tp','removed_fp']:assert s['gross_changes'][k]==sum(m['changes'][k] for m in metrics);checks+=1
                assert s['totals']['after']['tp']-s['totals']['before']['tp']==s['gross_changes']['new_tp']-s['gross_changes']['lost_tp']
                assert s['totals']['after']['fp']-s['totals']['before']['fp']==s['gross_changes']['new_fp']-s['gross_changes']['removed_fp']
    save(OUT/'summary-audit.json',dict(aggregate_fields_recomputed=checks,all_strata_including_zero_affected_replayed=True,net_gross_identities_verified=True))


if __name__=='__main__':run()
