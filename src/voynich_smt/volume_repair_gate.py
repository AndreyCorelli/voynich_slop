"""Separate source-calibrated repair gates for observed context-volume bands."""
from voynich_smt.combined_repair_gate import select


def fit_regimes(curve):
    chosen={}
    for regime,minimum in [('full',10),('sparse',20)]:
        candidates=[]
        for row in curve:
            s=row['stats'][regime]
            if s['calls']>=minimum and s['hit']/s['calls']>=.9 and s['clean_wrong']==0 and s['unavailable_wrong']==0:
                candidates.append(dict(policy=row['policy'],stats=s,qualified=True))
        chosen[regime]=max(candidates,key=lambda r:(r['stats']['hit'],-r['stats']['wrong'],-r['policy']['gap'],-r['policy']['stability'],r['policy']['threshold'])) if candidates else dict(policy=dict(threshold=None,gap=0.,stability=0.),qualified=False)
    return chosen


def route(n,bands):
    if n<=bands['maximum_short_sentences']:return 'sparse'
    if n>=bands['minimum_long_sentences']:return 'full'
    return None


def select_conditional(features,n,policies,bands):
    regime=route(n,bands)
    return None if regime is None else select(features,policies[regime])


def evaluate(cases,policies,bands):
    stats={r:dict(hit=0,wrong=0,calls=0,clean_wrong=0,unavailable_wrong=0,n=0) for r in sorted({c['regime'] for c in cases})}
    for c in cases:
        s=stats[c['regime']];s['n']+=1;pair=select_conditional(c['features'],c['context_sentences'],policies,bands);ref=c['reference'];hit=pair is not None and pair==ref['pair'];wrong=pair is not None and not hit
        s['hit']+=int(hit);s['wrong']+=int(wrong);s['calls']+=int(pair is not None);s['clean_wrong']+=int(wrong and not ref['error']);s['unavailable_wrong']+=int(wrong and ref['error'] and not ref['supported'])
    return stats
