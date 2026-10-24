"""Audit lexical masking, frozen PP inference, and fixed-cohort structural effects."""
from benchmarks.grammar_class_pp_utility_iteration120 import *


def run():
    hashes=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    public=load(ROOT/'iteration118/public.json');pred=load(ROOT/'iteration118/predictions.json')['full']['rows'];ids={r['opaque'] for r in pred};assignments=load(OUT/'assignments.json');cohorts=load(OUT/'cohorts.json');labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};settings=load(OUT/'settings.json');evaluation=load(OUT/'evaluation.json');scores={a:load(OUT/('scores-'+a+'.json')) for a in assignments};assert settings==SETTINGS;flat=[t for s in public for t in s['tokens']];assert cohorts==dict(all=list(range(len(flat))),original_unmapped=[i for i,t in enumerate(flat) if t['anchor'] is None],targets=[i for i,t in enumerate(flat) if t['id'] in ids],other_given_anchors=[i for i,t in enumerate(flat) if t['anchor'] is not None and t['id'] not in ids]);assert len(set(cohorts['original_unmapped'])|set(cohorts['targets'])|set(cohorts['other_given_anchors']))==9956
    recomputed=0;checks=0
    for arm,tags in assignments.items():
        view=load(OUT/('public-'+arm+'.json'));assert view==inject(public,ids,tags);assert all(t['anchor'] is None for s in view for t in s['tokens'] if t['id'] in ids)
        for s,t in zip(public,view):
            assert s['sent_id']==t['sent_id'] and len(s['tokens'])==len(t['tokens'])
            for a,b in zip(s['tokens'],t['tokens']):
                assert a['id']==b['id']
                if a['id'] not in ids:assert a==b
        for name,m in models.items():
            expected=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels),m)];assert np.allclose(expected,scores[arm][name],rtol=1e-12,atol=1e-12);recomputed+=1
        for name,cuts in settings.items():
            for policy,cut in cuts.items():
                before=np.array(scores['unknown'][name]);after=np.array(scores[arm][name]);gold=np.array([r['labels']['pp'] for r in labels])
                for c,ii in cohorts.items():
                    ix=np.array(ii);a=after[ix]>=cut;b=before[ix]>=cut;y=gold[ix];m=evaluation[arm][name][policy][c]['metrics'];expected=dict(tp=int((a&y).sum()),fp=int((a&~y).sum()),fn=int((~a&y).sum()),tn=int((~a&~y).sum()));assert all(m[k]==v for k,v in expected.items());assert m['precision']==(expected['tp']/(expected['tp']+expected['fp']) if expected['tp']+expected['fp'] else None);assert m['recall']==expected['tp']/(expected['tp']+expected['fn']);assert m['f1']==2*expected['tp']/(2*expected['tp']+expected['fp']+expected['fn'])
                    delta=dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()));assert delta==evaluation[arm][name][policy][c]['changes_from_unknown'];checks+=1
    # Private PP references are copied through infer85 but cannot affect scores.
    poisoned_labels=[dict(r,labels={'pp':not r['labels']['pp']}) for r in labels];view=load(OUT/'public-predicted.json');again=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,poisoned_labels),models['original'])];assert np.allclose(again,scores['predicted']['original'],rtol=1e-12,atol=1e-12)
    poisoned=[dict(s,tokens=[dict(t,anchor='POISON',tag='POISON') if t['id'] in ids else dict(t) for t in s['tokens']]) for s in public];assert inject(poisoned,ids,assignments['predicted'])==view
    gate_result=load(OUT/'utility-gate.json');u=evaluation['unknown']['original']['fixed80']['all']['metrics'];p=evaluation['predicted']['original']['fixed80']['all']['metrics'];sf=sum(evaluation['shuffle'+str(i)]['original']['fixed80']['all']['metrics']['f1'] for i in range(3))/3;expected=p['tp']>u['tp'] and p['f1']>u['f1'] and p['precision']>=.9 and p['f1']>sf;assert gate_result['passed']==expected==False and abs(gate_result['mean_shuffle_f1']-sf)<1e-12
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,all_pp_score_vectors_recomputed=recomputed,independent_fixed_cohort_confusion_and_transition_checks=checks,target_identities_hidden_all_arms=True,untargeted_inputs_unchanged=True,private_label_poison_invariance=True,input_target_identity_poison_invariance=True,predeclared_primary_gate_replayed=True,primary_gate_passed=False));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
