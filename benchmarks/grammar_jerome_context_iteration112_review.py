"""Replay frozen actions, pair bootstraps, and PP counts; summarize every stratum."""
from benchmarks.grammar_jerome_context_iteration112 import *
from benchmarks.grammar_context_shadow_pp_iteration105_audit import independent_counts


def run():
    hashes=0
    for name in ['design-freeze','context-freeze','pair-freeze','predictions-freeze']:
        for path,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(path)==h,path;hashes+=1
    cases=load(OUT/'pair-cases.json');evaluation=load(OUT/'evaluation.json');policies=load(OUT/'policies.json');bands=load(OUT/'routing.json');actions=load(OUT/'actions.json');publics={v:load(OUT/('public-'+v+'.json')) for v in ['base','expanded']};transforms=load(OUT/'transforms.json');labels=load(ROOT/'iteration97/jerome/reference-rows.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];bank=load(ROOT/'iteration98/calibration-bank.json');checks=0;groups={};wrong=[]
    for arm in policies:assert policies[arm]==load(ROOT/('iteration'+arm)/'policies.json')
    assert publics['expanded'][:100]==publics['base'] and len(publics['expanded'])==829
    reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not {s['sent_id'] for s in publics['expanded']}&reserved
    for c in cases:
        key=c['block']+'/'+c['case'];p=OUT/c['block']/(c['case']+'.npz');z=np.load(p);f=summarize(c['pairs'],z['draws']);assert f==c['features']
        for pi,(n,q) in enumerate(zip(z['counts'],z['sums'])):
            assert abs(float(gains_from_totals(n.sum(0),q.sum(0),c['proposed'][pi]))-c['pairs'][pi]['gain'])<1e-12
        context=perturb(publics[c['block']],bank[c['case']],anchors);before=context[:100];t=transforms[key];assert signature(before)==t['before']
        for arm,policy in policies.items():
            pair=select_conditional(c['features'],len(context),policy,bands);assert pair==actions[arm][key];after=repair_prefix(before,context,pair);info=t['arms'][arm];assert signature(after)==info['after'];r=evaluation[key][arm]
            if r['pair']['hit']:assert after==publics['base']
            if r['pair']['wrong']:wrong.append(dict(arm=arm,case=key,words=[c['identities'][i] for i in pair],affected=c['scored_affected_tokens'],supported=c['reference']['supported']))
            for model,cuts in PP_SETTINGS.items():
                for name,cut in cuts.items():
                    e=r['pp'][model][name]
                    for phase,sig in [('before',t['before']),('after',info['after']),('clean',signature(publics['base']))]:
                        probs=load(OUT/'pp-cache'/(sig+'.json'))['scores'][model]['pooled_pos'];expected=independent_counts(labels,probs,cut);assert all(e[phase][k]==v for k,v in expected.items());checks+=1
    for view in publics:
        errors=[c for c in cases if c['block']==view and c['reference']['error']]
        strata={'all_errors':errors,'affected_errors':[c for c in errors if c['scored_affected_tokens']],'zero_affected_errors':[c for c in errors if not c['scored_affected_tokens']],'supported_errors':[c for c in errors if c['reference']['supported']],'unsupported_errors':[c for c in errors if not c['reference']['supported']],'controls':[c for c in cases if c['block']==view and not c['reference']['error']]}
        for arm in policies:
            for name,cs in strata.items():
                rows=[evaluation[view+'/'+c['case']][arm] for c in cs];g=dict(n=len(rows),hit=sum(r['pair']['hit'] for r in rows),wrong=sum(r['pair']['wrong'] for r in rows),abstain=sum(r['pair']['abstain'] for r in rows),pp={})
                for model,cuts in PP_SETTINGS.items():
                    for policy in cuts:
                        ms=[r['pp'][model][policy] for r in rows];totals={phase:{k:sum(m[phase][k] for m in ms) for k in ['tp','fp','fn','tn']} for phase in ['before','after','clean']}
                        gross={k:sum(m['changes'][k] for m in ms) for k in ['new_tp','new_fp','lost_tp','removed_fp']}
                        assert totals['after']['tp']-totals['before']['tp']==gross['new_tp']-gross['lost_tp']
                        assert totals['after']['fp']-totals['before']['fp']==gross['new_fp']-gross['removed_fp']
                        g['pp'][model+'/'+policy]=dict(totals=totals,gross=gross,exact_clean_probability_cases=sum(m['maximum_probability_difference_from_clean']<=1e-12 for m in ms))
                groups[view+'/'+arm+'/'+name]=g
    save(OUT/'diagnostic-summary.json',dict(groups=groups,all_wrong_actions=wrong))
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,pair_bootstrap_replays=len(cases),blind_action_replays=len(cases)*len(policies),independent_confusion_checks=checks,no_reserve_ids=True,original_public_matches97=True))
    for view in publics:
        for arm in policies:
            g=groups[view+'/'+arm+'/all_errors'];a=groups[view+'/'+arm+'/affected_errors'];print(view,arm,g['hit'],g['wrong'],'affected',a['hit'],a['wrong'],'PP',a['pp']['original/fixed80'])
    print('WRONG',wrong)
if __name__=='__main__':run()
