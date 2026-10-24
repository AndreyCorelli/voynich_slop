"""Scalar candidate-quality flags calibrated without editing grammatical tags."""
import numpy as np


def calibrate_flag(scores,excluded,protected,budget=.01):
    """Maximize detected omissions within a false-flag budget on protected tags.

    Evaluate whole score-tie groups. Positive detection gain is required;
    ties prefer fewer flags. Inputs must already be calibration-only.
    """
    if not 0<=budget<=1:raise ValueError('budget must be in [0,1]')
    scores=np.asarray(scores);excluded=np.asarray(excluded,dtype=bool);protected=np.asarray(protected,dtype=bool)
    if not (scores.shape==excluded.shape==protected.shape) or not np.all(np.isfinite(scores)):raise ValueError('Aligned finite score arrays required')
    result=dict(enabled=False,threshold=None,budget=budget,calibration=dict(tokens=len(scores),excluded=int(excluded.sum()),protected=int(protected.sum()),flagged=0,flagged_excluded=0,false_flags_protected=0))
    if not len(scores) or not excluded.any():return result
    order=np.argsort(-scores,kind='stable');s=scores[order];ends=np.r_[np.flatnonzero(s[1:]!=s[:-1]),len(s)-1];tp=np.cumsum(excluded[order]);fp=np.cumsum(protected[order]);best=(0,0,0.)
    for end in ends:
        if fp[end]>budget*protected.sum():continue
        key=(int(tp[end]),-int(end+1),float(s[end]))
        if key>best:
            best=key;result.update(enabled=True,threshold=float(s[end]));result['calibration'].update(flagged=int(end+1),flagged_excluded=int(tp[end]),false_flags_protected=int(fp[end]))
    return result


def flag(scores,policy):
    return np.asarray(scores)>=policy['threshold'] if policy['enabled'] else np.zeros(len(scores),bool)


def abstention_metrics(predicted,gold,excluded,flagged):
    pred=np.asarray(predicted);gold=np.asarray(gold);excluded=np.asarray(excluded,dtype=bool);flagged=np.asarray(flagged,dtype=bool);correct=pred==gold;keep=~flagged;n=len(gold);nf=int(flagged.sum());nk=int(keep.sum());ne=int(excluded.sum());protected=correct&~excluded
    keptcorrect=int((correct&keep).sum());flagcorrect=int((correct&flagged).sum());flagexcluded=int((excluded&flagged).sum());fp=int((protected&flagged).sum())
    return dict(tokens=n,baseline_correct=int(correct.sum()),baseline_accuracy=float(correct.mean()) if n else None,
        flagged=nf,retained=nk,retained_correct=keptcorrect,coverage=nk/n if n else None,retained_accuracy=keptcorrect/nk if nk else None,retained_correct_fraction=keptcorrect/n if n else None,
        excluded=ne,flagged_excluded=flagexcluded,excluded_precision=flagexcluded/nf if nf else None,excluded_recall=flagexcluded/ne if ne else None,
        flagged_errors=int((flagged&~correct).sum()),flagged_error_precision=int((flagged&~correct).sum())/nf if nf else None,
        correct_tags_discarded=flagcorrect,protected_correct=int(protected.sum()),false_flags_protected=fp,false_flag_rate_protected=fp/int(protected.sum()) if protected.any() else None)
