"""Replay every blind action and model input; independently count PP transitions."""
from benchmarks.grammar_context_shadow_pp_iteration105 import *


def independent_counts(reference,probabilities,cut,mask=None):
    out=dict(tp=0,fp=0,fn=0,tn=0)
    for i,(r,p) in enumerate(zip(reference,probabilities)):
        if mask is not None and not mask[i]:continue
        gold=r['labels']['pp'];pred=p>=cut;out['tp' if gold and pred else 'fp' if pred else 'fn' if gold else 'tn']+=1
    return out


def run():
    hashes=0
    for manifest in [OUT/'design-freeze.json',OUT/'predictions-freeze.json',PREVIOUS/'verification-manifest.json']:
        for path,h in load(manifest)['inputs'].items():assert digest(Path(path))==h,path;hashes+=1
    public=load(OUT/'public-clean.json');assert public==load(PREVIOUS/'public-base.json');assert len(public)==100 and sum(len(s['tokens']) for s in public)==1514
    labels=load(OUT/'reference-rows.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};payloads={p.stem:load(p) for p in (OUT/'pp-cache').glob('*.json') if not p.name.endswith('.freeze.json')};predictions=0
    for sig,payload in payloads.items():
        view=apply_delta(public,payload['delta']);assert signature(view)==sig
        for arm,m in models.items():
            inferred=compact(infer85(query_rows(view,labels),m));saved=payload['scores'][arm]
            assert np.allclose(inferred['pooled_pos'],saved['pooled_pos'],rtol=1e-12,atol=1e-12);assert inferred['left']==saved['left'];assert inferred['prior']==saved['prior'];predictions+=1
    transforms=load(OUT/'transforms.json');actions=load(PREVIOUS/'actions.json');cases=load(PREVIOUS/'evaluation-cases.json');bank=load(ROOT/'iteration98/calibration-bank.json');evaluation=load(OUT/'evaluation.json');clean_sig=signature(public);clean=payloads[clean_sig]['scores'];count_checks=0;applied=0;hits=0
    for c in cases:
        key=c['block']+'/'+c['case'];before_public=perturb(public,bank[c['case']],anchors);info=transforms[key];assert signature(before_public)==info['before'];before=payloads[info['before']]['scores']
        for arm,action in info['arms'].items():
            assert action['pair']==actions[arm][key];after_public=swap_assignments(before_public,action['pair']);assert signature(after_public)==action['after'];assert len(after_public)==100
            assert action['changed_tokens']==sum(x!=y for s,t in zip(before_public,after_public) for x,y in zip(s['tokens'],t['tokens']));assert [t['id'] for s in after_public for t in s['tokens']]==[t['id'] for s in public for t in s['tokens']]
            after=payloads[action['after']]['scores'];r=evaluation[key][arm];pair=action['pair'];hit=pair is not None and pair==c['reference']['pair'];assert r['pair']['hit']==int(hit);assert r['pair']['wrong']==int(pair is not None and not hit);applied+=1;hits+=int(hit)
            if hit:assert after_public==public
            for model,cuts in PP_SETTINGS.items():
                for policy,cut in cuts.items():
                    e=r['pp'][model][policy];new=after[model]['pooled_pos'];old=before[model]['pooled_pos'];cl=clean[model]['pooled_pos']
                    for phase,prob in [('before',old),('after',new),('clean',cl)]:
                        expected=independent_counts(labels,prob,cut);assert all(e[phase][k]==v for k,v in expected.items());count_checks+=1
                    expected=independent_counts(labels,new,cut,[r['anchor'] is None for s in after_public for r in s['tokens']]);assert all(e['hidden_after'][k]==v for k,v in expected.items())
                    changes=dict(new_tp=0,new_fp=0,lost_tp=0,removed_fp=0)
                    for ref,p,q in zip(labels,new,old):
                        if p>=cut and q<cut:changes['new_tp' if ref['labels']['pp'] else 'new_fp']+=1
                        if p<cut and q>=cut:changes['lost_tp' if ref['labels']['pp'] else 'removed_fp']+=1
                    assert changes==e['changes'];assert e['different_from_clean']==sum((p>=cut)!=(q>=cut) for p,q in zip(new,cl));assert e['maximum_probability_difference_from_clean']==max(abs(p-q) for p,q in zip(new,cl))
                    if hit:assert e['maximum_probability_difference_from_clean']==0
    for model,path in [('original',ROOT/'iteration86/caesar-195/predictions.json'),('augmented',ROOT/'iteration89/caesar-correct/predictions.json')]:
        old=load(path);assert [(r['sid'],r['index'],r['labels']) for r in old]==[(r['sid'],r['index'],r['labels']) for r in labels];assert np.allclose([r['scores']['pooled_pos']['pp'] for r in old],clean[model]['pooled_pos'],rtol=1e-12,atol=1e-12)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,blind_case_arm_actions_replayed=applied,unique_model_inferences_recomputed=predictions,independent_confusion_count_checks=count_checks,exact_repair_probability_restorations=hits,old_clean_predictions_match=True,fixed100_positions_only=True,all_transitions_and_hidden_counts_verified=True,no_truth_gate_or_new_annotations_or_reserve=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
