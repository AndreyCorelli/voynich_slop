"""Descriptive calibration failure analysis; no policy changes or target selection."""
from benchmarks.grammar_repair_abstention_iteration98 import *

def build():
    cases=load(OUT/'calibration-cases.json');old=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'];byblock={}
    for block in sorted({c['block'] for c in cases}):byblock[block]=evaluate_cal([c for c in cases if c['block']==block],old,0.)['full' if block=='full' else 'sparse']
    diagnostic={}
    for arm in ('absolute','margin'):
        curve=load(OUT/('calibration-curve-'+arm+'.json'));support=lambda r:r['stats']['full']['calls']>=10 and r['stats']['sparse']['calls']>=20;precision=lambda r:all(s['calls'] and s['hit']/s['calls']>=.9 for s in r['stats'].values());sampled=[r for r in curve if support(r)];best=max(sampled,key=lambda r:r['stats']['sparse']['hit']/r['stats']['sparse']['calls']);diagnostic[arm]=dict(candidate_policies=len(curve),meeting_minimum_calls=len(sampled),meeting_minimum_calls_and_precision=sum(support(r) and precision(r) for r in curve),descriptive_max_sparse_precision_policy=best)
    evaluation={}
    values=load(OUT/'evaluation.json')
    for name in ('source','Jerome','Caesar'):
        evaluation[name]={}
        for arm in ('absolute','margin','frozen95'):
            rows=[v[arm] for k,v in values.items() if k.startswith(name+'/swap_')];evaluation[name][arm]=dict(cases=len(rows),hit=sum(r['pair']['hit'] for r in rows),wrong=sum(r['pair']['wrong'] for r in rows),abstain=sum(r['pair']['abstain'] for r in rows),all_pp_unchanged=all(not any(e['changes'].values()) for r in rows for p in r['pp'].values() for e in p.values()))
    return dict(frozen95_calibration_by_block=byblock,calibration_failure_diagnostics=diagnostic,evaluation=evaluation)

if __name__=='__main__':
    result=build();assert result['frozen95_calibration_by_block']==load(OUT/'frozen95-calibration-by-block.json');save(OUT/'summary.json',result);save(OUT/'summary-audit.json',dict(calibration_and_evaluation_aggregates_recomputed=True,descriptive_diagnostics_not_selected_policies=True));print('Summary verified')
