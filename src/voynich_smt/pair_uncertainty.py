"""Sentence-cluster bootstrap of fixed, jointly masked pair probabilities."""
import numpy as np
from voynich_smt import anchor_grammar as ag
from voynich_smt.paired_anchor_class import target_features
from voynich_smt.repair_abstention import pair_features


def gains_from_totals(counts, sums, proposed):
    """counts/sums end in the two endpoints; sums are P(CCONJ) totals."""
    valid=np.all(counts>0,axis=-1)
    p=np.divide(sums,counts,out=np.zeros_like(sums,dtype=float),where=counts>0)
    # Match disagreement's additive epsilon, rather than clipping probabilities.
    margin=np.log((p+1e-12)/(1-p+1e-12))
    gain=(margin*np.asarray([1 if tag=='ADP' else -1 for tag in proposed])).sum(axis=-1)
    return np.where(valid,gain,-np.inf)


def sentence_totals(public,pair,model):
    rows=target_features(public,set(pair));q=ag.predict([r['features'] for r in rows],model)
    positions={s['sent_id']:i for i,s in enumerate(public)};ends={opaque:i for i,opaque in enumerate(pair)}
    counts=np.zeros((len(public),2));sums=np.zeros_like(counts)
    for r,p in zip(rows,q):
        j,k=positions[r['sid']],ends[r['word']];counts[j,k]+=1;sums[j,k]+=p[1]
    return counts,sums


def summarize(pairs,draws):
    """Selection uncertainty conditional on original count-eligible candidate set."""
    features=pair_features(pairs);eligible=[j for j,p in enumerate(pairs) if p['supported']]
    if features['pair'] is None:return dict(features,stability=0.,lower_gain=None,lower_gap=None,valid_fraction=0.)
    j=next(j for j,p in enumerate(pairs) if p['pair']==features['pair']);gain=draws[:,j]
    rivals=[k for k in eligible if k!=j]
    rival=np.max(draws[:,rivals],axis=1) if rivals else np.full(len(draws),-np.inf)
    valid=np.isfinite(gain);gap=gain-rival
    # Ties and missing selected endpoints are failures, not discarded draws.
    wins=valid & (gain>rival) & ~np.isclose(gain,rival,rtol=1e-12,atol=1e-12)
    def lower(values):
        ordered=np.sort(values);value=ordered[int(np.floor(.05*(len(values)-1)))];return float(value) if np.isfinite(value) else None
    return dict(features,stability=float(wins.mean()),lower_gain=lower(gain),lower_gap=lower(np.where(valid,gap,-np.inf)),valid_fraction=float(valid.mean()))


def selected(features,policy):
    if policy.get('threshold') is None or features['pair'] is None:return None
    if policy['arm']=='stability':
        return features['pair'] if features['gain']>=policy['threshold'] and features['stability']>=policy['stability'] else None
    if policy['arm']=='lower':
        return features['pair'] if features['lower_gain'] is not None and features['lower_gap'] is not None and features['lower_gain']>=policy['threshold'] and features['lower_gap']>=0 else None
    return features['pair'] if features['gain']>=policy['threshold'] and (features['gap'] is None or features['gap']>=policy.get('gap',0)) else None


def evaluate(cases,policy):
    stats={regime:dict(hit=0,wrong=0,calls=0,clean_wrong=0,unavailable_wrong=0,n=0) for regime in sorted({c['regime'] for c in cases})}
    for c in cases:
        s=stats[c['regime']];s['n']+=1;p=selected(c['features'],policy);r=c['reference'];hit=p is not None and p==r['pair'];wrong=p is not None and not hit
        s['hit']+=int(hit);s['wrong']+=int(wrong);s['calls']+=int(p is not None);s['clean_wrong']+=int(wrong and not r['error']);s['unavailable_wrong']+=int(wrong and r['error'] and not r['supported'])
    return stats


def calibrate(cases,arm):
    key='lower_gain' if arm=='lower' else 'gain'
    thresholds=sorted({0.}|{c['features'][key] for c in cases if c['features'][key] is not None and c['features'][key]>=0});curve=[]
    for threshold in thresholds:
        for stability in ((.5,.75,.9,.95,.99,1.) if arm=='stability' else (0.,)):
            policy=dict(arm=arm,threshold=threshold,stability=stability);stats=evaluate(cases,policy)
            minimum_ok=all(stats[r]['calls']>=minimum for r,minimum in [('full',10),('sparse',20)])
            precision_ok=minimum_ok and all(s['hit']/s['calls']>=.9 for s in stats.values())
            qualified=precision_ok and all(s['clean_wrong']==0 and s['unavailable_wrong']==0 for s in stats.values())
            curve.append(dict(policy=policy,stats=stats,minimum_ok=minimum_ok,precision_ok=precision_ok,qualified=qualified))
    eligible=[r for r in curve if r['qualified']]
    chosen=max(eligible,key=lambda r:(sum(s['hit'] for s in r['stats'].values()),-sum(s['wrong'] for s in r['stats'].values()),r['policy']['threshold'],r['policy']['stability'])) if eligible else dict(policy=dict(arm=arm,threshold=None),qualified=False)
    return chosen,curve
