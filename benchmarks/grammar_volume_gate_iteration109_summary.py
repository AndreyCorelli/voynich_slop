"""Volume-conditioned outcomes, including all unavailable and zero-affected errors."""
from benchmarks.grammar_volume_gate_iteration109 import *


def run():
    cases=load(PREVIOUS/'pair-cases.json');evaluation=load(OUT/'evaluation.json');base={c['case']:c for c in cases if c['block']=='base'};groups={};wrong=[]
    for view in ['base','civil','expanded']:
        errors=[c for c in cases if c['block']==view and c['reference']['error']]
        for name,cs in {'all_errors':errors,'affected_errors':[c for c in errors if c['scored_affected_tokens']>0],'zero_affected_errors':[c for c in errors if not c['scored_affected_tokens']],'available_errors':[c for c in errors if c['reference']['pair'] is not None]}.items():
            rows=[evaluation[view+'/'+c['case']] for c in cs];result=dict(cases=len(rows),hit=sum(r['pair']['hit'] for r in rows),wrong=sum(r['pair']['wrong'] for r in rows),abstain=sum(r['pair']['abstain'] for r in rows),pp={})
            for model,cuts in PP_SETTINGS.items():
                for policy in cuts:
                    ms=[r['pp'][model][policy] for r in rows];totals={phase:{k:sum(m[phase][k] for m in ms) for k in ['tp','fp','fn','tn']} for phase in ['before','after','clean']}
                    for t in totals.values():t.update(precision=t['tp']/(t['tp']+t['fp']) if t['tp']+t['fp'] else None,recall=t['tp']/(t['tp']+t['fn']) if t['tp']+t['fn'] else 0.)
                    gross={k:sum(m['changes'][k] for m in ms) for k in ['new_tp','new_fp','lost_tp','removed_fp']};assert totals['after']['tp']-totals['before']['tp']==gross['new_tp']-gross['lost_tp'];assert totals['after']['fp']-totals['before']['fp']==gross['new_fp']-gross['removed_fp']
                    result['pp'][model+'/'+policy]=dict(totals=totals,gross_changes=gross,cases_matching_clean_probabilities=sum(m['maximum_probability_difference_from_clean']<=1e-12 for m in ms),decision_differences_from_clean=sum(m['different_from_clean'] for m in ms))
            groups[view+'/'+name]=result
    for c in cases:
        key=c['block']+'/'+c['case'];r=evaluation[key]
        if r['pair']['wrong']:wrong.append(dict(case=key,selected_words=[c['identities'][i] for i in r['pair']['selected']],scored_affected_tokens=c['scored_affected_tokens'],reference_supported=c['reference']['supported'],features=c['features'],pp=r['pp']))
    prior=load(PREVIOUS/'evaluation.json');comparison={}
    for view in ['base','civil','expanded']:
        rows=[arms['frozen95'] for key,arms in prior.items() if key.startswith(view+'/') and key.split('/')[1].startswith('swap_')];comparison[view]=dict(frozen95_hit=sum(r['pair']['hit'] for r in rows),frozen95_wrong=sum(r['pair']['wrong'] for r in rows),conditional=groups[view+'/all_errors'])
    source_curve=load(CURVE/'calibration-curve.json');qualifying={}
    for regime,minimum in [('full',10),('sparse',20)]:qualifying[regime]=sum(r['stats'][regime]['calls']>=minimum and r['stats'][regime]['hit']/r['stats'][regime]['calls']>=.9 and r['stats'][regime]['clean_wrong']==0 and r['stats'][regime]['unavailable_wrong']==0 for r in source_curve)
    save(OUT/'diagnostic-summary.json',dict(groups=groups,all_wrong_actions=wrong,comparison_to107=comparison,qualifying_grid_settings_by_regime=qualifying,limits='Separatepolicyexperiment, not108sharedguardpassing; shortOFF, onlylongactive. ReusedadaptiveCaesarcases, ≥829segmentsnotguaranteepertypeevidence. Countsrepeatpositions; no newcleangramcoverage/nuclei.'))
    for view in ['base','civil','expanded']:
        r=groups[view+'/all_errors'];a=groups[view+'/affected_errors'];print(view,'all',r['hit'],r['wrong'],'affected',a['hit'],a['wrong'],'PP',a['pp']['original/fixed80'])
    print('wrong',[(r['case'],r['selected_words'],r['reference_supported']) for r in wrong]);print('qualifying source settings',qualifying)
if __name__=='__main__':run()
