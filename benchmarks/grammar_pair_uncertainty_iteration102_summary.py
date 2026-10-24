"""Descriptive diagnostics; never change the frozen OFF policies."""
from benchmarks.grammar_pair_uncertainty_iteration102 import *


def run():
    output={}
    for arm in ['stability','lower']:
        curve=load(OUT/('curve-'+arm+'.json'));supported=[r for r in curve if r['minimum_ok']]
        best=max(supported,key=lambda r:(min(s['hit']/s['calls'] for s in r['stats'].values()),sum(s['hit'] for s in r['stats'].values()))) if supported else None
        zerowrong=[r for r in curve if all(s['wrong']==0 for s in r['stats'].values()) and r['stats']['full']['calls']>=10]
        output[arm]=dict(candidates=len(curve),minimum_coverage_candidates=len(supported),precision_candidates=sum(r['precision_ok'] for r in curve),best_worst_regime_precision_with_minimum_coverage=best,maximum_sparse_zero_wrong_with_10full=max(zerowrong,key=lambda r:(r['stats']['sparse']['calls'],r['stats']['full']['calls'])) if zerowrong else None)
    cal=load(OUT/'calibration-cases.json');cut=load(ROOT/'iteration95/policies.json')['joint_context']['threshold']
    output['descriptive_oldcut_stability90']=evaluate102(cal,dict(arm='stability',threshold=cut,stability=.9))
    # The designated failure's full wrong-pair stability distribution, not only a favorable example.
    cases=load(OUT/'evaluation-cases.json');bad=[c for c in cases if c['block']=='200-0' and c['reference']['error'] and c['features']['gain'] is not None and c['features']['gain']>=cut and c['features']['pair']!=c['reference']['pair']]
    output['bad_merge_wrong_recommendations']=[dict(case=c['case'],stability=c['features']['stability'],lower_gap=c['features']['lower_gap']) for c in bad]
    output['interpretation']='Both calibrated policies OFF. Descriptive90%stability screen gives sparse11correct/0wrong versus96/172 oldcut, full24/0vs50/0; insufficient20sparsecallguard, correlated development data, not certified/adopted. Best supported precision improves over98gain/gap but below90%. No target-selected policies or restoration gain.'
    save(OUT/'diagnostic-summary.json',output);print(json.dumps(output,indent=2))
if __name__=='__main__':run()
