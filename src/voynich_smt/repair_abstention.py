"""Calibrate repair abstention against diverse errors and unavailable partners."""
import math

GAPS=(0.,.1,.25,.5,1.)


def pair_features(pairs):
    supported=sorted((r for r in pairs if r['supported']),key=lambda r:r['gain'],reverse=True)
    if not supported:return dict(pair=None,gain=None,gap=None)
    best=supported[0]
    tied=len(supported)>1 and math.isclose(best['gain'],supported[1]['gain'],rel_tol=1e-12,abs_tol=1e-12)
    return dict(pair=None if tied else best['pair'],gain=best['gain'],gap=best['gain']-supported[1]['gain'] if len(supported)>1 else None)


def select(features,threshold,gap):
    if threshold is None or features['pair'] is None:return None
    if features['gain']<threshold:return None
    if features['gap'] is not None and features['gap']<gap:return None
    return features['pair']


def evaluate(cases,threshold,gap):
    result={k:dict(hit=0,wrong=0,calls=0,clean_wrong=0,unavailable_wrong=0,n=0) for k in ('full','sparse')}
    for c in cases:
        r=result[c['regime']];r['n']+=1;pair=select(c['features'],threshold,gap);hit=pair is not None and c['reference']['pair'] is not None and pair==c['reference']['pair'];wrong=pair is not None and not hit;r['hit']+=int(hit);r['wrong']+=int(wrong);r['calls']+=pair is not None;r['clean_wrong']+=wrong and not c['reference']['error'];r['unavailable_wrong']+=wrong and c['reference']['error'] and not c['reference']['supported']
    return result


def calibrate(cases,allow_gap):
    thresholds=sorted({0.}|{c['features']['gain'] for c in cases if c['features']['pair'] is not None and c['features']['gain']>=0})+[None];curve=[]
    for threshold in thresholds:
        for gap in GAPS if allow_gap else (0.,):
            stats=evaluate(cases,threshold,gap);qualified=all(s['calls']>=minimum and s['hit']/s['calls']>=.9 and s['clean_wrong']==0 and s['unavailable_wrong']==0 for s,minimum in ((stats['full'],10),(stats['sparse'],20)));curve.append(dict(threshold=threshold,gap=gap,qualified=qualified,stats=stats))
    eligible=[r for r in curve if r['qualified']]
    if not eligible:return dict(threshold=None,gap=0.,qualified=False,stats=evaluate(cases,None,0.)),curve
    chosen=max(eligible,key=lambda r:(sum(s['hit'] for s in r['stats'].values()),-sum(s['wrong'] for s in r['stats'].values()),-r['gap'],r['threshold']))
    return chosen,curve
