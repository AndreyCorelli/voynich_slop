"""Enumerate source-calibration decision sets without a coarse score grid."""
from voynich_smt.anchor_class_audit import metrics


def exact_policy(clean,corrupted):
    thresholds=sorted({0.}|{r['disagreement'] for r in clean+corrupted if r['supported'] and r['disagreement']>=0})+[float('inf')]
    curve=[];tokens=sum(r['n'] for r in clean)
    for threshold in thresholds:
        c=metrics(clean,threshold);e=metrics(corrupted,threshold)
        curve.append(dict(threshold=None if threshold==float('inf') else threshold,clean=c,corrupted=e,eligible=c['fp']<=1 and c['flagged_tokens']<=.05*tokens))
    selected=max((r for r in curve if r['eligible']),key=lambda r:(r['corrupted']['tp'],-r['corrupted']['fp'],-r['clean']['flagged_tokens'],float('inf') if r['threshold'] is None else r['threshold']))
    return selected,curve
