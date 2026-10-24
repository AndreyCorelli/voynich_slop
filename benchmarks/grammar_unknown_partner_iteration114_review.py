"""Replay source calibration/transfer and independently audit singleton scores."""
from benchmarks.grammar_unknown_partner_iteration114 import *
from voynich_smt.paired_anchor_class import target_features


def independent_singletons(public,candidates,model):
    result={}
    for opaque in sorted(candidates):
        rows=target_features(public,{opaque});n=len(rows)
        if not n:continue
        q=ag.predict([r['features'] for r in rows],model);prob=float(np.mean(q[:,1]));ns=len({r['sid'] for r in rows});tag=next(t['tag'] for s in public for t in s['tokens'] if t['id']==opaque);gain=math.log((prob+1e-12)/(1-prob+1e-12))*(1 if tag=='ADP' else -1);result[opaque]=dict(gain=gain,n=n,sentences=ns,supported=n>=5 and ns>=3)
    return result


def run():
    hashes=0
    for name in ['design-freeze','policy-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    source=load(ROOT/'iteration110/cases.json');singles=load(OUT/'source-singletons.json');base=load(ROOT/'iteration111/policies.json')['full'];curve=load(OUT/'calibration-curve.json');chosen=load(OUT/'chosen.json');eligible=[]
    for r in curve:
        c=stats([x for x in source if x['regime']=='complete'],singles,base,r['cutoff']);o=stats([x for x in source if x['regime']=='omission'],singles,base,r['cutoff']);assert c==r['complete'] and o==r['omission'];ok=c['hit']>=39 and o['hit']>=540 and o['distinct_hits']>=20 and all(s['calls'] and s['hit']/s['calls']>=.9 and s['clean_wrong']==0 and s['unsupported_wrong']==0 for s in [c,o]);assert ok==r['qualified']
        if ok:eligible.append(r)
    expected=max(eligible,key=lambda r:(r['complete']['hit'],r['omission']['hit'],r['omission']['distinct_hits'],-r['complete']['wrong']-r['omission']['wrong'],r['cutoff'])) if eligible else dict(cutoff=None,qualified=False);assert expected==chosen
    ids=load(ROOT/'iteration98/blocks.json')['scored']['full'];d=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];public=ag.public_sentences([dict(sent_id=i,**d[i]) for i in ids],anchors,'cal98-full');words=load(ROOT/'iteration93/types.json')['candidates'];candidates={t['id'] for s in public for t in s['tokens'] if t['anchor'] in words};model=load(ROOT/'iteration93/models.json')['context'];bank=load(ROOT/'iteration98/calibration-bank.json');checks=0
    def verify(p,stored):
        nonlocal checks
        expected=independent_singletons(p,candidates,model);assert set(expected)==set(stored)
        for i,r in expected.items():
            assert all(r[k]==stored[i][k] for k in ['n','sentences','supported']);assert abs(r['gain']-stored[i]['gain'])<1e-11;checks+=1
    for case,ss in singles.items():verify(perturb(public,bank[case],anchors),ss)
    rows=load(OUT/'challenge-cases.json');cached=load(OUT/'challenge-singletons.json');old={(r['removed_word'],r['case']):r for r in load(ROOT/'iteration113/cases.json')};seen=set();actions=0;summary={};rejected={a:[] for a in ['calibrated','zero_diagnostic']};mistake={}
    for r in rows:
        key=r['removed_word']+'/'+r['case'];ss=cached.get(key,{});prior=old[r['removed_word'],r['case']];assert r['features']==prior['features'] and r['reference']==prior['reference'];assert r['base_pair']==gate(r['features'],base)
        if ss and (r['removed_word'] not in seen or (r['base_pair'] is not None and r['base_pair']!=r['reference']['pair'])):
            p=load(ROOT/'iteration113'/('public-'+r['removed_word']+'.json'));verify(perturb(p,bank[r['case']],anchors),ss);seen.add(r['removed_word'])
        for arm,cut in [('calibrated',chosen['cutoff']),('zero_diagnostic',0.)]:
            # Independent gate expression; base abstention is preserved.
            alt=max([0.]+[x['gain'] for x in ss.values() if x['supported']]);value=None if r['features']['pair'] is None else r['features']['gain']-alt;pair=r['base_pair'] if cut is not None and r['base_pair'] is not None and value>=cut else None;assert pair==r['actions'][arm];actions+=1
            if r['base_pair'] is not None and pair is None:rejected[arm].append(dict(removed_word=r['removed_word'],case=r['case'],was_correct=r['base_pair']==r['reference']['pair'],contrast=r['contrast']))
        if r['base_pair'] is not None and r['base_pair']!=r['reference']['pair']:
            mistake=dict(case=key,contrast=r['contrast'],pair_gain=r['features']['gain'],singleton_best=max([0.]+[x['gain'] for x in ss.values() if x['supported']]),singletons=ss)
    groups={'all_errors':[r for r in rows if r['reference']['error']],'supported_errors':[r for r in rows if r['reference']['error'] and r['reference']['supported']],'unsupported_errors':[r for r in rows if r['reference']['error'] and not r['reference']['supported']],'literal_absence_errors':[r for r in rows if r['true_endpoint_absent']],'controls':[r for r in rows if not r['reference']['error']]}
    for g,rr in groups.items():
        summary[g]={}
        for arm in ['base','calibrated','zero_diagnostic']:
            selected=lambda r:r['base_pair'] if arm=='base' else r['actions'][arm]
            hit=sum(selected(r) is not None and selected(r)==r['reference']['pair'] for r in rr);wrong=sum(selected(r) is not None and selected(r)!=r['reference']['pair'] for r in rr);summary[g][arm]=dict(n=len(rr),hit=hit,wrong=wrong,abstain=len(rr)-hit-wrong)
    sourcezero={g:stats([r for r in source if r['regime']==g],singles,base,0.) for g in ['complete','omission']}
    # Post-hoc explanation only: these clean scores never affect the gate.
    p=load(ROOT/'iteration113/public-sine.json');names={t['id']:t['anchor'] for s in p for t in s['tokens'] if t['anchor'] in words};cl=independent_singletons(p,candidates,model);bad=cached['sine/swap_sine__sed']
    save(OUT/'matched-clean-diagnostic.json',dict(posthoc=True,not_used_for_policy_or_challenge_selection=True,removed_word='sine',case='swap_sine__sed',singleton_gains={names[i]:dict(clean_gain=cl[i]['gain'],corrupt_gain=bad[i]['gain'],change=bad[i]['gain']-cl[i]['gain']) for i in cl}))
    save(OUT/'summary.json',dict(groups=summary,zero_diagnostic_source=sourcezero,rejected_actions=rejected,false_fallback_mechanism=mistake));save(OUT/'audit.json',dict(input_hashes_verified=hashes,source_cutoffs_replayed=len(curve),qualifying_cutoffs=len(eligible),independent_singleton_scores_verified=checks,challenge_actions_independently_replayed=actions,challenge_views_sampled_for_inference=len(seen)));print('SUMMARY',summary);print('ZERO SOURCE',sourcezero);print('AUDIT',load(OUT/'audit.json'))
if __name__=='__main__':run()
