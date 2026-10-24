"""Source-calibrated conjunction of pair gain, runner-up gap and rank stability."""
from voynich_smt.repair_abstention import GAPS

STABILITIES=(.5,.75,.9,.95,.99,1.)


def select(features,policy):
    if policy['threshold'] is None or features['pair'] is None:return None
    if features['gain']<policy['threshold'] or features['stability']<policy['stability']:return None
    if features['gap'] is not None and features['gap']<policy['gap']:return None
    return features['pair']


def evaluate(cases,policy):
    stats={r:dict(hit=0,wrong=0,calls=0,clean_wrong=0,unavailable_wrong=0,n=0) for r in sorted({c['regime'] for c in cases})}
    for c in cases:
        s=stats[c['regime']];s['n']+=1;pair=select(c['features'],policy);ref=c['reference'];hit=pair is not None and pair==ref['pair'];wrong=pair is not None and not hit
        s['hit']+=int(hit);s['wrong']+=int(wrong);s['calls']+=int(pair is not None);s['clean_wrong']+=int(wrong and not ref['error']);s['unavailable_wrong']+=int(wrong and ref['error'] and not ref['supported'])
    return stats


def calibrate(cases):
    thresholds=sorted({0.}|{c['features']['gain'] for c in cases if c['features']['pair'] is not None and c['features']['gain']>=0});curve=[]
    for threshold in thresholds:
        for gap in GAPS:
            for stability in STABILITIES:
                policy=dict(threshold=threshold,gap=gap,stability=stability);stats=evaluate(cases,policy)
                minimum_ok=all(stats[r]['calls']>=minimum for r,minimum in [('full',10),('sparse',20)])
                precision_ok=minimum_ok and all(s['hit']/s['calls']>=.9 for s in stats.values())
                qualified=precision_ok and all(s['clean_wrong']==0 and s['unavailable_wrong']==0 for s in stats.values())
                curve.append(dict(policy=policy,stats=stats,minimum_ok=minimum_ok,precision_ok=precision_ok,qualified=qualified))
    eligible=[r for r in curve if r['qualified']]
    chosen=max(eligible,key=lambda r:(sum(s['hit'] for s in r['stats'].values()),-sum(s['wrong'] for s in r['stats'].values()),-r['policy']['gap'],-r['policy']['stability'],r['policy']['threshold'])) if eligible else dict(policy=dict(threshold=None,gap=0.,stability=0.),qualified=False)
    return chosen,curve
