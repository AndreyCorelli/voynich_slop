"""Calibrate a long-context gate with complete and omitted-candidate negatives."""
from voynich_smt.combined_repair_gate import select,evaluate,STABILITIES
from voynich_smt.repair_abstention import GAPS


def calibrate(cases):
    thresholds=sorted({0.}|{r['features']['gain'] for r in cases if r['features']['pair'] is not None and r['features']['gain']>=0});curve=[]
    for threshold in thresholds:
        for gap in GAPS:
            for stability in STABILITIES:
                policy=dict(threshold=threshold,gap=gap,stability=stability);stats=evaluate(cases,policy)
                distinct={r['case'] for r in cases if r['regime']=='omission' and r['reference']['error'] and select(r['features'],policy) is not None}
                distinct_hits={r['case'] for r in cases if r['regime']=='omission' and r['reference']['error'] and select(r['features'],policy) is not None and select(r['features'],policy)==r['reference']['pair']}
                coverage_ok=stats['complete']['calls']>=10 and len(distinct)>=20
                precision_ok=coverage_ok and all(s['hit']/s['calls']>=.9 for s in stats.values())
                qualified=precision_ok and all(s['clean_wrong']==0 and s['unavailable_wrong']==0 for s in stats.values())
                curve.append(dict(policy=policy,stats=stats,distinct_omission_cases=len(distinct),distinct_omission_hits=len(distinct_hits),coverage_ok=coverage_ok,precision_ok=precision_ok,qualified=qualified))
    eligible=[r for r in curve if r['qualified']]
    chosen=max(eligible,key=lambda r:(r['stats']['complete']['hit'],r['distinct_omission_hits'],-sum(s['wrong'] for s in r['stats'].values()),-r['policy']['gap'],-r['policy']['stability'],r['policy']['threshold'])) if eligible else dict(policy=dict(threshold=None,gap=0.,stability=0.),qualified=False)
    return chosen,curve
