"""Independent vectorized calibration audit and no-op/blind target replay."""
from benchmarks.grammar_combined_gate_iteration108 import *
from benchmarks.grammar_context_shadow_pp_iteration105_audit import independent_counts


def run():
    hashes=0
    for manifest in [OUT/'design-freeze.json',OUT/'policy-freeze.json',OUT/'predictions-freeze.json',CAL/'verification-manifest.json',PREVIOUS/'verification-manifest.json']:
        for path,h in load(manifest)['inputs'].items():assert digest(Path(path))==h,path;hashes+=1
    cases=load(CAL/'calibration-cases.json');features=[c['features'] for c in cases];gain=np.array([f['gain'] if f['gain'] is not None else -np.inf for f in features]);gap=np.array([f['gap'] if f['gap'] is not None else np.inf for f in features]);stability=np.array([f['stability'] for f in features]);present=np.array([f['pair'] is not None for f in features]);hit=np.array([f['pair'] is not None and f['pair']==c['reference']['pair'] for f,c in zip(features,cases)]);clean=np.array([not c['reference']['error'] for c in cases]);unavailable=np.array([c['reference']['error'] and not c['reference']['supported'] for c in cases]);regimes=np.array([c['regime'] for c in cases]);curve=load(OUT/'calibration-curve.json')
    for r in curve:
        p=r['policy'];called=present&(gain>=p['threshold'])&(gap>=p['gap'])&(stability>=p['stability']);stats={}
        for regime in ['full','sparse']:
            mask=regimes==regime;calls=called&mask;wrong=calls&~hit;stats[regime]=dict(hit=int((calls&hit).sum()),wrong=int(wrong.sum()),calls=int(calls.sum()),clean_wrong=int((wrong&clean).sum()),unavailable_wrong=int((wrong&unavailable).sum()),n=int(mask.sum()))
        assert stats==r['stats'];minimum=stats['full']['calls']>=10 and stats['sparse']['calls']>=20;precision=minimum and all(s['hit']/s['calls']>=.9 for s in stats.values());qualified=precision and all(s['clean_wrong']==0 and s['unavailable_wrong']==0 for s in stats.values());assert (minimum,precision,qualified)==(r['minimum_ok'],r['precision_ok'],r['qualified'])
    chosen,replayed=calibrate108(cases);assert replayed==curve and chosen==load(OUT/'chosen.json');policy=load(OUT/'policy.json');assert chosen['policy']==policy
    targets=load(PREVIOUS/'pair-cases.json');transforms=load(OUT/'transforms.json');evaluation=load(OUT/'evaluation.json');actions={c['block']+'/'+c['case']:select108(c['features'],policy) for c in targets};assert actions==load(OUT/'actions.json');assert evaluate108(targets,policy)==load(OUT/'pair-summary.json');labels=load(ROOT/'iteration105/reference-rows.json');public=load(PREVIOUS/'public-base.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];bank=load(ROOT/'iteration98/calibration-bank.json');publics={v:load(PREVIOUS/('public-'+v+'.json')) for v in ['base','civil','expanded']};sources=load(OUT/'cache-sources.json');payloads={}
    for sig,source in sources.items():
        payload=load(OUT/'pp-cache'/(sig+'.json'));assert source!='new' and payload==load(source);assert signature(apply_delta(public,payload['delta']))==sig;payloads[sig]=payload
    checks=0
    for c in targets:
        key=c['block']+'/'+c['case'];context=perturb(publics[c['block']],bank[c['case']],anchors);before=context[:100];after=repair_prefix(before,context,actions[key]);t=transforms[key];assert signature(before)==t['before'] and signature(after)==t['after'];assert t['pair']==actions[key];r=evaluation[key];assert r['changed_tokens']==sum(x!=y for s,z in zip(before,after) for x,y in zip(s['tokens'],z['tokens']))
        for model,cuts in PP_SETTINGS.items():
            for name,cut in cuts.items():
                for phase,sig in [('before',t['before']),('after',t['after'])]:
                    expected=independent_counts(labels,payloads[sig]['scores'][model]['pooled_pos'],cut);assert all(r['pp'][model][name][phase][k]==v for k,v in expected.items());checks+=1
        if policy['threshold'] is None:
            assert before==after and r['pair']['selected'] is None and r['changed_tokens']==0
            for model,cuts in PP_SETTINGS.items():
                for name in cuts:
                    e=r['pp'][model][name];assert e['before']==e['after'];assert all(v==0 for v in e['changes'].values())
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,independent_vectorized_policy_checks=len(curve),calibration_refit_identical=True,blind_author_actions_replayed=len(targets),independent_confusion_count_checks=checks,cached_prediction_payloads_verified=len(payloads),all_off_actions_unchanged=policy['threshold'] is None,no_new_annotations_or_reserve=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
