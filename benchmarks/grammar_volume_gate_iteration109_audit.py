"""Independently audit regime selection, volume routing and blind PP actions."""
from benchmarks.grammar_volume_gate_iteration109 import *
from benchmarks.grammar_context_shadow_pp_iteration105_audit import independent_counts


def run():
    hashes=0
    for manifest in [OUT/'design-freeze.json',OUT/'policy-freeze.json',OUT/'predictions-freeze.json',CURVE/'verification-manifest.json',PREVIOUS/'verification-manifest.json']:
        for path,h in load(manifest)['inputs'].items():assert digest(Path(path))==h,path;hashes+=1
    curve=load(CURVE/'calibration-curve.json');chosen=load(OUT/'chosen.json');policies=load(OUT/'policies.json');bands=load(OUT/'routing.json');blocks=load(ROOT/'iteration98/blocks.json')['scored'];assert bands==dict(maximum_short_sentences=max(len(ids) for k,ids in blocks.items() if k!='full'),minimum_long_sentences=len(blocks['full']));eligible_counts={}
    for regime,minimum in [('full',10),('sparse',20)]:
        eligible=[]
        for r in curve:
            s=r['stats'][regime]
            if s['calls']>=minimum and s['hit']>=.9*s['calls'] and s['clean_wrong']==0 and s['unavailable_wrong']==0:eligible.append(dict(policy=r['policy'],stats=s,qualified=True))
        expected=max(eligible,key=lambda r:(r['stats']['hit'],-r['stats']['wrong'],-r['policy']['gap'],-r['policy']['stability'],r['policy']['threshold'])) if eligible else dict(policy=dict(threshold=None,gap=0.,stability=0.),qualified=False)
        assert expected==chosen[regime] and policies[regime]==expected['policy'];eligible_counts[regime]=len(eligible)
    assert fit_regimes(curve)==chosen
    source=[dict(c,context_sentences=len(blocks[c['block']])) for c in load(CAL/'calibration-cases.json')];assert evaluate109(source,policies,bands)==load(OUT/'calibration-summary.json')
    publics={v:load(PREVIOUS/('public-'+v+'.json')) for v in ['base','civil','expanded']};targets=[dict(c,context_sentences=len(publics[c['block']])) for c in load(PREVIOUS/'pair-cases.json')];actions={};routes={}
    for v,p in publics.items():
        n=len(p);r='sparse' if n<=100 else 'full' if n>=829 else None;assert r==route(n,bands);routes[v]=dict(sentences=n,route=r)
    assert routes==load(OUT/'routes.json')
    for c in targets:
        r=routes[c['block']]['route'];p=None if r is None else policies[r];f=c['features'];expected=None
        if p is not None and p['threshold'] is not None and f['pair'] is not None and f['gain']>=p['threshold'] and f['stability']>=p['stability'] and (f['gap'] is None or f['gap']>=p['gap']):expected=f['pair']
        assert expected==select_conditional(f,c['context_sentences'],policies,bands);actions[c['block']+'/'+c['case']]=expected
    assert actions==load(OUT/'actions.json');assert evaluate109(targets,policies,bands)==load(OUT/'pair-summary.json')
    public=publics['base'];labels=load(ROOT/'iteration105/reference-rows.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];bank=load(ROOT/'iteration98/calibration-bank.json');sources=load(OUT/'cache-sources.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};payloads={};new_inferences=0
    for sig,source_path in sources.items():
        payload=load(OUT/'pp-cache'/(sig+'.json'));view=apply_delta(public,payload['delta']);assert signature(view)==sig and len(view)==100
        if source_path!='new':assert payload==load(source_path)
        else:
            for a,m in models.items():
                expected=compact(infer85(query_rows(view,labels),m));assert np.allclose(expected['pooled_pos'],payload['scores'][a]['pooled_pos'],rtol=1e-12,atol=1e-12);assert expected['left']==payload['scores'][a]['left'];new_inferences+=1
        payloads[sig]=payload
    clean=payloads[signature(public)]['scores'];evaluation=load(OUT/'evaluation.json');transforms=load(OUT/'transforms.json');checks=0;exact_affected=0
    for c in targets:
        key=c['block']+'/'+c['case'];context=perturb(publics[c['block']],bank[c['case']],anchors);before=context[:100];after=repair_prefix(before,context,actions[key]);t=transforms[key];assert signature(before)==t['before'] and signature(after)==t['after'] and t['pair']==actions[key];r=evaluation[key];hit=actions[key] is not None and actions[key]==c['reference']['pair'];assert r['pair']['hit']==int(hit) and r['pair']['wrong']==int(actions[key] is not None and not hit);assert r['changed_tokens']==sum(x!=y for s,z in zip(before,after) for x,y in zip(s['tokens'],z['tokens']))
        if hit:assert after==public
        if hit and c['scored_affected_tokens']:exact_affected+=1
        if c['block']=='base':assert before==after and actions[key] is None
        for a,cuts in PP_SETTINGS.items():
            for name,cut in cuts.items():
                e=r['pp'][a][name];new=payloads[t['after']]['scores'][a]['pooled_pos'];old=payloads[t['before']]['scores'][a]['pooled_pos'];cl=clean[a]['pooled_pos']
                for phase,prob in [('before',old),('after',new),('clean',cl)]:
                    expected=independent_counts(labels,prob,cut);assert all(e[phase][k]==v for k,v in expected.items());checks+=1
                expected=independent_counts(labels,new,cut,[t['anchor'] is None for s in after for t in s['tokens']]);assert all(e['hidden_after'][k]==v for k,v in expected.items())
                changes=dict(new_tp=0,new_fp=0,lost_tp=0,removed_fp=0)
                for ref,p,q in zip(labels,new,old):
                    if p>=cut and q<cut:changes['new_tp' if ref['labels']['pp'] else 'new_fp']+=1
                    if p<cut and q>=cut:changes['lost_tp' if ref['labels']['pp'] else 'removed_fp']+=1
                assert changes==e['changes'];assert e['different_from_clean']==sum((p>=cut)!=(q>=cut) for p,q in zip(new,cl));assert e['maximum_probability_difference_from_clean']==max(abs(p-q) for p,q in zip(new,cl))
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,independent_source_setting_checks=2*len(curve),eligible_settings_by_regime=eligible_counts,conditional_actions_and_routes_replayed=len(targets),independent_confusion_count_checks=checks,cached_payloads_verified=len(payloads),new_model_inferences_recomputed=new_inferences,exact_affected_probability_restorations_across_views=exact_affected,short_context_noop=True,no_new_annotations_or_reserve=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
