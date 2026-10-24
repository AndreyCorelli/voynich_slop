"""Independent replay of the bounded scalar-gate ceiling."""
from benchmarks.grammar_adp_gate_ceiling_iteration123 import *

def run():
    hashes=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():
            assert digest(p)==h,p
            hashes+=1
    public=load(ROOT/'iteration118/public.json'); rows=load(ROOT/'iteration118/predictions.json')['full']['rows'];prob={r['opaque']:r['probabilities']['balanced13'] for r in rows}
    def tags_at(c,ps=prob):return {i:('CCONJ' if p>.5 else 'ADP') for i,p in ps.items() if p>.5 or 1-p>=c}
    labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')]; y=np.array([r['labels']['pp'] for r in labels],dtype=bool)
    cohorts=load(PREVIOUS/'cohorts.json');settings=load(PREVIOUS/'settings.json');old=load(PREVIOUS/'scores-predicted.json');evaluation=load(OUT/'evaluation.json');curve=load(OUT/'oracle-test-curve.json');seen=set();vectors=checks=0
    assert [r['threshold'] for r in curve]==sorted({0.,1.}|{1-p for p in prob.values() if p<=.5})
    for r in curve:
        assert tags_at(r['threshold'])==r['tags'];sig=r['assignment'];view=load(OUT/('public-'+sig+'.json'));assert view==inject(public,set(prob),r['tags'])
        if sig in seen:continue
        seen.add(sig);scores=load(OUT/('scores-'+sig+'.json'))
        for name,model in [('original',load(BASE/'models.json')),('augmented',load(ROOT/'iteration89/models.json'))]:
            expected=[v['scores']['pooled_pos']['pp'] for v in infer85(query_rows(view,labels),model)];assert np.allclose(expected,scores[name],rtol=1e-12,atol=1e-12);vectors+=1
            for policy,cut in settings[name].items():
                for cohort,ii in cohorts.items():
                    a=np.array(scores[name])[ii]>=cut;b=np.array(old[name])[ii]>=cut;t=y[ii];e=evaluation[sig][name][policy][cohort];m=e['metrics']
                    assert [m[k] for k in ['tp','fp','fn','tn']]==[int((a&t).sum()),int((a&~t).sum()),int((~a&t).sum()),int((~a&~t).sum())]
                    assert m['precision']==(m['tp']/(m['tp']+m['fp']) if m['tp']+m['fp'] else None)
                    assert e['changes_from_ungated']==dict(new_tp=int((a&~b&t).sum()),new_fp=int((a&~b&~t).sum()),lost_tp=int((~a&b&t).sum()),removed_fp=int((~a&b&~t).sum()));checks+=1
    baseline=curve[0]['metrics'];minimum=math.ceil(.8*baseline['tp']);assert minimum==188
    for r in curve:
        assert r['metrics']==evaluation[r['assignment']]['original']['fixed80']['all']['metrics'];assert r['oracle_qualifies']==qualifies(r['metrics'],baseline)
    assert not any(r['oracle_qualifies'] for r in curve)
    calprob=load(CAL/'calibration-probabilities.json');calcurve=load(CAL/'calibration-curve.json');calstates={tagkey(r['tags']):r['metrics'] for r in calcurve};teststates={tagkey(r['tags']):r['metrics'] for r in curve};joint=load(OUT/'joint-feasibility.json');points=sorted({0.,1.}|{1-p for p in prob.values() if p<=.5}|{1-p for p in calprob.values() if p<=.5});assert [r['threshold'] for r in joint]==points
    for j,r in enumerate(joint):
        assert r['interval_upper_inclusive']==points[j] and r['interval_lower_exclusive']==(points[j-1] if j else None)
        for cut in [points[j]]+([(points[j-1]+points[j])/2] if j else []):
            assert teststates[tagkey(tags_at(cut))]==r['test_metrics'];assert calstates[tagkey(tags_at(cut,calprob))]==r['calibration_metrics']
        assert r['test_qualifies']==qualifies(r['test_metrics'],baseline);assert r['calibration_qualifies']==qualifies(r['calibration_metrics'],calcurve[0]['metrics']);assert r['jointly_qualifies']==(r['test_qualifies'] and r['calibration_qualifies'])
    best=max((r for r in curve if r['metrics']['precision']>=.9),key=lambda r:(r['metrics']['tp'],-r['metrics']['fp'],r['threshold']));nontrivial=max(r['metrics']['tp'] for r in curve if r['withheld']);assert nontrivial==185<minimum
    save(OUT/'diagnostic-summary.json',dict(oracle_only=True,minimum_required_tp=minimum,maximum_tp_after_any_abstention=nontrivial,best_high_precision=best,high_precision_tp_retention=best['metrics']['tp']/baseline['tp'],tp_shortfall=minimum-best['metrics']['tp'],bounded_family_infeasible=True))
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,pp_score_vectors_recomputed=vectors,independent_metric_and_transition_groups=checks,thresholds_replayed=len(curve),joint_intervals_replayed=len(joint),all_checks_passed=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
