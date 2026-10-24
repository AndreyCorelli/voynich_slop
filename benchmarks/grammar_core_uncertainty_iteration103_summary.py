"""Descriptive coverage limits and block-wise transfer; no policy changes."""
from benchmarks.grammar_core_uncertainty_iteration103 import *


def run():
    summary={}
    for arm in ['stability','lower']:
        curve=load(OUT/('curve-'+arm+'.json'));supported=[r for r in curve if r['minimum_ok']];clean=[r for r in curve if all(s['wrong']==0 for s in r['stats'].values())]
        summary[arm]=dict(candidates=len(curve),minimum_coverage_candidates=len(supported),precision_candidates=sum(r['precision_ok'] for r in curve),best_minimum_supported=min(supported,key=lambda r:-min(s['hit']/s['calls'] for s in r['stats'].values())) if supported else None,largest_zero_wrong=max(clean,key=lambda r:sum(s['hit'] for s in r['stats'].values())) if clean else None)
    evaluation=load(OUT/'evaluation-summary.json');summary['evaluation_by_length']={}
    for arm,blocks in evaluation.items():
        group={}
        for block,row in blocks.items():
            size=block.split('-')[0];acc=group.setdefault(size,{k:0 for k in row})
            for k,v in row.items():acc[k]+=v
        summary['evaluation_by_length'][arm]=group
    summary['limits']='Nested/correlated reused development blocks; calibratedcore was selected using calibration99. NoPPintegration/newrestoration/nuclei. BothuncertaintypoliciesOFF; gain_gap qualifiescal but misses90percenton100sentenceevaluation. No policy/guard changes after target inspection.'
    save(OUT/'diagnostic-summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
