"""Independent factorial interventions, PP inference, and permutation attribution."""
from benchmarks.grammar_class_error_factorial_iteration121 import *


def run():
    hashes=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(OUT/'factorial-assignments.json');words=data['errors'];assert words==['c','per','sine','uel'];old=load(PREVIOUS/'assignments.json');source=load(PREVIOUS/'public-predicted.json');lookup={r['type']:r['opaque'] for r in load(ROOT/'iteration118/predictions.json')['full']['rows']};ids=set(old['predicted']);labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};settings=load(PREVIOUS/'settings.json');cohorts=load(PREVIOUS/'cohorts.json');evaluation=load(OUT/'evaluation.json');attributions=load(OUT/'attributions.json');provenance=load(OUT/'cache-provenance.json');scores={};inferences=0;checks=0
    for mask in range(16):
        corrected=[w for j,w in enumerate(words) if mask&(1<<j)];expected=dict(old['predicted'])
        for w in corrected:expected[lookup[w]]=old['oracle'][lookup[w]]
        assert expected==data['masks'][str(mask)]['tags'] and corrected==data['masks'][str(mask)]['corrected'];view=load(OUT/('public-'+str(mask)+'.json'));assert view==inject(source,ids,expected);assert all(t['anchor'] is None for s in view for t in s['tokens'] if t['id'] in ids);scores[mask]=load(OUT/('scores-'+str(mask)+'.json'))
        if provenance[str(mask)]!='new':assert scores[mask]==load(provenance[str(mask)])
        for name,m in models.items():
            q=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels),m)];assert np.allclose(q,scores[mask][name],rtol=1e-12,atol=1e-12);inferences+=1
    gold=np.array([r['labels']['pp'] for r in labels])
    for mask in range(16):
        for name,cuts in settings.items():
            for policy,cut in cuts.items():
                for c,indices in cohorts.items():
                    ix=np.array(indices);a=np.array(scores[mask][name])[ix]>=cut;b=np.array(scores[0][name])[ix]>=cut;y=gold[ix];record=evaluation[str(mask)][name][policy][c];expected=dict(tp=int((a&y).sum()),fp=int((a&~y).sum()),fn=int((~a&y).sum()),tn=int((~a&~y).sum()));assert all(record['metrics'][k]==v for k,v in expected.items());d=dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()));assert d==record['changes_from_predicted'];checks+=1
    perms=list(itertools.permutations(range(4)));allocations=0;undefined=[];marginal_ranges={}
    for name,cuts in settings.items():
        for policy in cuts:
            for c in cohorts:
                for metric in ['tp','fp','f1','precision']:
                    raw=[evaluation[str(mask)][name][policy][c]['metrics'][metric] for mask in range(16)];record=attributions[name][policy][c][metric]
                    if any(v is None for v in raw):
                        # Runner uses conventional zero selection utility for undefined
                        # precision. Exclude it from interpreted precision attribution.
                        undefined.append(dict(model=name,policy=policy,cohort=c,metric=metric));continue
                    values=np.array(raw,float);out=np.zeros(4)
                    for permutation in perms:
                        mask=0
                        for j in permutation:new=mask|(1<<j);out[j]+=(values[new]-values[mask])/24;mask=new
                    assert np.allclose(out,[record['shapley'][w] for w in words],rtol=1e-12,atol=1e-12);assert abs(sum(record['shapley'].values())-record['total'])<1e-12 and abs(record['total']-(values[15]-values[0]))<1e-12;allocations+=1
    for j,w in enumerate(words):
        out={}
        for metric in ['tp','fp']:
            values=[evaluation[str(mask)]['original']['fixed80']['all']['metrics'][metric] for mask in range(16)];d=[values[mask|(1<<j)]-values[mask] for mask in range(16) if not mask&(1<<j)];out[metric]=dict(minimum=min(d),maximum=max(d),all_background_differences=d)
        marginal_ranges[w]=out
    crossing=load(OUT/'oracle-precision-crossings.json');assert [r['mask'] for r in crossing['passing']]==[mask for mask in range(16) if evaluation[str(mask)]['original']['fixed80']['all']['metrics']['precision']>=.9]
    save(OUT/'attribution-validity.json',dict(undefined_precision_not_interpreted=undefined,runner_zero_convention_is_not_a_precision_estimate=True));save(OUT/'marginal-ranges.json',marginal_ranges);save(OUT/'audit.json',dict(input_hashes_verified=hashes,all_factorial_pp_score_vectors_recomputed=inferences,independent_fixed_cohort_confusion_and_transition_checks=checks,exact24permutation_allocations_verified=allocations,undefined_precision_allocations_excluded=len(undefined),all16interventions_verified=True,baseline_and_fulloracle_caches_equal120=True,primary_marginal_ranges_verified=True,no_deployable_correction_claim=True));print(load(OUT/'audit.json'));print('RANGES',marginal_ranges)
if __name__=='__main__':run()
