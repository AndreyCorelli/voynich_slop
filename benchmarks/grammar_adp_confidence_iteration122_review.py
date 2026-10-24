"""Audit source-only confidence selection and unchanged test transformation."""
from benchmarks.grammar_adp_confidence_iteration122 import *


def run():
    hashes=0
    for name in ['design-freeze','calibration-input-freeze','calibration-predictions-freeze','policy-freeze','test-input-freeze','test-predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    public=load(OUT/'calibration-public-original.json');profiles=load(OUT/'calibration-profiles.json');prob=load(OUT/'calibration-probabilities.json');words=load(ROOT/'iteration93/types.json')['candidates'];lookup={w:hashlib.sha256(('cal122|'+w).encode()).hexdigest() for w in words};hidden=set(lookup.values());model=load(ROOT/'iteration116/class-models.json')['final'];calibrator=load(ROOT/'iteration117/models.json')['balanced13'];expected=grouped_profile(public,words,lookup,hidden,model)
    for w,p in expected.items():
        assert p['n']==profiles[w]['n'] and p['sentences']==profiles[w]['sentences'];assert abs(p['mean']-profiles[w]['mean'])<1e-12;assert abs(float(apply_offset([p['mean']],calibrator)[0])-prob[lookup[w]])<1e-12
    part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert [s['sent_id'] for s in public]==part['calibration'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not {s['sent_id'] for s in public}&(set(part['fit'])|set(part['test'])|reserved)
    labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'calibration-predictions.json')];ppmodel=load(BASE/'models.json');curve=load(OUT/'calibration-curve.json');eligible=[];seen=set();inferences=0;checks=0;baseline=next(r for r in curve if r['threshold']==0.)['metrics'];indices=list(range(len(labels)));unmapped=[i for i,t in enumerate(t for s in public for t in s['tokens']) if t['anchor'] is None]
    for r in curve:
        tags={i:('CCONJ' if p>.5 else 'ADP') for i,p in prob.items() if p>.5 or 1-p>=r['threshold']};assert tags==r['tags'];view=load(OUT/('calibration-public-'+r['assignment']+'.json'));assert view==inject(public,hidden,tags);scores=load(OUT/('calibration-scores-'+r['assignment']+'.json'))
        if r['assignment'] not in seen:
            predicted=[v['scores']['pooled_pos']['pp'] for v in infer85(query_rows(view,labels),ppmodel)];assert np.allclose(predicted,scores,rtol=1e-12,atol=1e-12);seen.add(r['assignment']);inferences+=1
        for name,ii in [('metrics',indices),('unmapped_metrics',unmapped)]:
            p=np.array(scores)[ii]>=.8;y=np.array([labels[i]['labels']['pp'] for i in ii]);m=r[name];assert m['tp']==int((p&y).sum()) and m['fp']==int((p&~y).sum()) and m['fn']==int((~p&y).sum()) and m['tn']==int((~p&~y).sum());assert m['precision']==(m['tp']/(m['tp']+m['fp']) if m['tp']+m['fp'] else None);checks+=1
        ok=r['metrics']['precision'] is not None and r['metrics']['precision']>=.9 and r['metrics']['tp']>=math.ceil(.8*baseline['tp']);assert ok==r['qualified']
        if ok:eligible.append(r)
    chosen=load(OUT/'chosen.json');best=max(eligible,key=lambda r:(r['metrics']['tp'],-r['metrics']['fp'],r['threshold'])) if eligible else dict(threshold=None,qualified=False);assert best==chosen
    test=load(ROOT/'iteration118/public.json');pred=load(ROOT/'iteration118/predictions.json')['full']['rows'];tt={r['opaque']:('CCONJ' if r['probabilities']['balanced13']>.5 else 'ADP') for r in pred if r['probabilities']['balanced13']>.5 or chosen['threshold'] is None or 1-r['probabilities']['balanced13']>=chosen['threshold']};view=load(OUT/'test-public.json');assert view==inject(test,{r['opaque'] for r in pred},tt);assert tt==load(OUT/'test-assignments.json')['tags'];testlabels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];scores=load(OUT/'test-scores.json');old=load(PREVIOUS/'scores-predicted.json');unknown=load(PREVIOUS/'scores-unknown.json');cohorts=load(PREVIOUS/'cohorts.json');evaluation=load(OUT/'evaluation.json');settings=load(PREVIOUS/'settings.json')
    for name,m in [('original',ppmodel),('augmented',load(ROOT/'iteration89/models.json'))]:
        expected=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,testlabels),m)];assert np.allclose(expected,scores[name],rtol=1e-12,atol=1e-12);inferences+=1
        for policy,cut in settings[name].items():
            for c,ii in cohorts.items():
                a=np.array(scores[name])[ii]>=cut;y=np.array([testlabels[i]['labels']['pp'] for i in ii]);e=evaluation[name][policy][c];m=e['metrics'];assert m['tp']==int((a&y).sum()) and m['fp']==int((a&~y).sum()) and m['fn']==int((~a&y).sum()) and m['tn']==int((~a&~y).sum())
                for comp,q in [('ungated',old),('unknown',unknown)]:
                    b=np.array(q[name])[ii]>=cut;d=dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()));assert d==e['changes_from_'+comp];checks+=1
    result=load(OUT/'result.json');assert result['test_passed']==(chosen['qualified'] and result['selected']['precision']>=.9 and result['selected']['tp']>=math.ceil(.8*result['baseline']['tp']))
    source_names={i:w for w,i in lookup.items()};anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];cal_wrong=[dict(type=source_names[i],predicted='CCONJ' if p>.5 else 'ADP',reference=anchors[source_names[i]],confidence=max(p,1-p)) for i,p in prob.items() if ('CCONJ' if p>.5 else 'ADP')!=anchors[source_names[i]]];test_wrong=[dict(type=r['type'],predicted='CCONJ' if r['probabilities']['balanced13']>.5 else 'ADP',reference=anchors[r['type']],confidence=max(r['probabilities']['balanced13'],1-r['probabilities']['balanced13'])) for r in pred if ('CCONJ' if r['probabilities']['balanced13']>.5 else 'ADP')!=anchors[r['type']]];save(OUT/'error-pattern-diagnostic.json',dict(posthoc_not_used_for_selection=True,calibration=cal_wrong,test=test_wrong,minimum_test_ADP_confidence=min(1-r['probabilities']['balanced13'] for r in pred if r['probabilities']['balanced13']<=.5)))
    same=view==load(PREVIOUS/'public-predicted.json');assert same and all(np.allclose(scores[a],old[a],rtol=1e-12,atol=1e-12) for a in scores)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,class_profiles_recomputed=16,pp_score_vectors_recomputed=inferences,independent_confusion_and_transition_checks=checks,calibration_thresholds_replayed=len(curve),selected_policy_matches_source_only_objective=True,test_input_and_scores_identical_to120_ungated=True,primary_test_guard_failed=True,no_author_scoring_or_default_change=True));print(load(OUT/'audit.json'));print('CAL WRONG',cal_wrong);print('TEST WRONG',test_wrong)
if __name__=='__main__':run()
