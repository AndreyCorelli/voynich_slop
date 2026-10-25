"""Independent exhaustive source-frontier and fixed-test-policy audit."""
from benchmarks.grammar_posterior_threshold_iteration128 import *

def run():
    hashes=0
    for name in ['design-freeze','policy-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    labels=load(BASE/'calibration-predictions.json');scores=load(PREVIOUS/'calibration/scores.json');p=np.array(scores['posterior']);y=np.array([r['labels']['pp'] for r in labels],bool);curve=load(OUT/'calibration-frontier.json');assert [r['threshold'] for r in curve]==sorted(set(p)|{1.});hard=np.array(scores['hard'])>=.8;baseline=(int((hard&y).sum()),int((hard&~y).sum()));assert baseline==(310,25);minimum=math.ceil(.8*baseline[0]);eligible=[]
    for r in curve:
        a=p>=r['threshold'];tp=int((a&y).sum());fp=int((a&~y).sum());assert (tp,fp)==(r['tp'],r['fp']);assert r['precision']==(tp/(tp+fp) if tp+fp else None);ok=tp>=minimum and 10*tp>=9*(tp+fp);assert ok==r['qualified']
        if ok:eligible.append(r)
    chosen=load(OUT/'chosen.json');assert chosen==max(eligible,key=lambda r:(r['tp'],-r['fp'],r['threshold']));summary=load(OUT/'summary.json');assert summary['qualified_settings']==len(eligible) and summary['settings']==len(curve);assert summary['maximum_tp_at90precision']==max((r for r in curve if r['tp']+r['fp'] and 10*r['tp']>=9*(r['tp']+r['fp'])),key=lambda r:(r['tp'],-r['fp'],r['threshold']));assert summary['best_precision_with_required_coverage']==max((r for r in curve if r['tp']>=minimum),key=lambda r:(r['precision'],r['tp'],r['threshold']))
    labels=load(BASE/'predictions.json');scores=load(PREVIOUS/'test/scores.json');cohorts=load(ROOT/'iteration120/cohorts.json');old=load(ROOT/'iteration120/scores-predicted.json')['original'];evaluation=load(OUT/'evaluation.json');checks=0
    for c,ii in cohorts.items():
        a=np.array(scores['posterior'])[ii]>=chosen['threshold'];y=np.array([labels[i]['labels']['pp'] for i in ii],bool);e=evaluation[c];m=e['metrics'];assert [m[k] for k in ['tp','fp','fn','tn']]==[int((a&y).sum()),int((a&~y).sum()),int((~a&y).sum()),int((~a&~y).sum())];assert m['precision']==(m['tp']/(m['tp']+m['fp']) if m['tp']+m['fp'] else None)
        for key,base in [('hard',scores['hard']),('unknown',scores['unknown']),('previous',old)]:
            b=np.array(base)[ii]>=.8;assert e['changes_from_'+key]==dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()));checks+=1
    result=load(OUT/'result.json');assert result['selected']==evaluation['all']['metrics'];assert result['passed']==(result['selected']['precision']>=.9 and result['selected']['tp']>=196);assert not result['passed']
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,source_thresholds_independently_replayed=len(curve),source_qualified_settings=len(eligible),selection_replayed=True,test_cohort_transition_comparisons=checks,test_threshold_matches_source_selected=True,test_guard_failed=True,no_new_inference_or_default_change=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
