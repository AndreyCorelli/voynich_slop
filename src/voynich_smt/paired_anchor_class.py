"""Blind pair enumeration and joint-masked contextual class consistency."""
import math
import numpy as np
from voynich_smt import anchor_grammar as ag
from voynich_smt.anchor_class_audit import disagreement

ARMS=('joint_context','independent_context','prior','shuffle0','shuffle1','shuffle2')


def target_features(public,target_ids):
    """Equivalent to public_features with both target types masked, selected rows only."""
    rows=[]
    for s in public:
        ts=s['tokens'];names=[None if t['id'] in target_ids else t['anchor'] for t in ts];tags=['X' if t['id'] in target_ids else t['tag'] for t in ts];words=[w or 'OPAQUE' for w in names]
        for i,t in enumerate(ts):
            if t['id'] not in target_ids:continue
            features=ag.government_features(words,tags,[0.]*len(ts),i,True)+['centerAnchorTag:X']
            for d in (-4,-3,-2,-1,1,2,3,4):
                j=i+d
                if 0<=j<len(ts) and names[j] is not None:features.append('anchor'+str(d)+':'+names[j])
            rows.append(dict(sid=s['sent_id'],index=i,word=t['id'],anchor_tag='X',features=features))
    return rows


def pair_scores(public,records,models):
    """No reference pair, class truth or word identities are accepted."""
    proposed={r['anchor_id']:r for r in records};adps=[r for r in records if r['proposed']=='ADP'];conjs=[r for r in records if r['proposed']=='CCONJ'];result={a:[] for a in ARMS}
    for a in adps:
        for c in conjs:
            ids={a['anchor_id'],c['anchor_id']};rows=target_features(public,ids);xx=[r['features'] for r in rows];indices={opaque:[i for i,r in enumerate(rows) if r['word']==opaque] for opaque in ids};supported=a['supported'] and c['supported'];pair=sorted(ids)
            for arm in ARMS:
                if arm=='independent_context':gain=a['disagreement']+c['disagreement']
                else:
                    modelarm='context' if arm=='joint_context' else arm
                    q=np.tile(models['prior'],(len(rows),1)) if arm=='prior' else ag.predict(xx,models[modelarm]);gain=0.
                    for opaque in ids:
                        mean=q[indices[opaque]].mean(axis=0).tolist();margin,_=disagreement(mean,['ADP','CCONJ'],proposed[opaque]['proposed']);gain+=margin
                result[arm].append(dict(pair=pair,gain=float(gain),supported=supported))
    return result


def recommend(pairs,threshold):
    eligible=[r for r in pairs if r['supported'] and r['gain']>=threshold]
    if not eligible:return None
    best=max(r['gain'] for r in eligible);winners=[r for r in eligible if math.isclose(r['gain'],best,rel_tol=1e-12,abs_tol=1e-12)]
    return winners[0]['pair'] if len(winners)==1 else None


def pair_metrics(pairs,threshold,reference):
    selected=recommend(pairs,threshold);true_pair=reference['pair'];is_error=reference['error'];hit=selected is not None and true_pair is not None and selected==true_pair
    return dict(hit=int(hit),false_pair=int(selected is not None and not hit),miss=int(is_error and not hit),selected=selected,error=is_error,reference_present=true_pair is not None,reference_supported=any(r['supported'] and r['pair']==true_pair for r in pairs),candidate_pairs=len(pairs),supported_pairs=sum(r['supported'] for r in pairs))


def calibrate_pair(clean,corrupted,clean_ref,corrupt_ref):
    thresholds=sorted({0.}|{r['gain'] for r in clean+corrupted if r['supported'] and r['gain']>=0})+[float('inf')];curve=[]
    for threshold in thresholds:
        c=pair_metrics(clean,threshold,clean_ref);e=pair_metrics(corrupted,threshold,corrupt_ref);curve.append(dict(threshold=None if math.isinf(threshold) else threshold,clean=c,corrupted=e,eligible=c['false_pair']==0))
    chosen=max((r for r in curve if r['eligible']),key=lambda r:(r['corrupted']['hit'],-r['corrupted']['false_pair'],float('inf') if r['threshold'] is None else r['threshold']))
    return chosen,curve
