"""Contextual ADP/CCONJ disagreement with a proposed anchor class."""
import math

THRESHOLDS=(0.,.5,1.,2.,3.,4.,8.,float('inf'))


def disagreement(mean, classes, proposed):
    assert proposed in ('ADP','CCONJ')
    opposite='CCONJ' if proposed=='ADP' else 'ADP'
    a=mean[classes.index(proposed)];b=mean[classes.index(opposite)]
    return math.log((b+1e-12)/(a+1e-12)),a+b


def flagged(record, threshold):
    return record['supported'] and record['disagreement']>=threshold


def metrics(records,threshold):
    tp=fp=fn=tn=unsupported_errors=flagged_tokens=0
    for r in records:
        wrong=r['class_wrong'];flag=flagged(r,threshold)
        tp+=wrong and flag;fp+=not wrong and flag;fn+=wrong and not flag;tn+=not wrong and not flag
        unsupported_errors+=wrong and not r['supported'];flagged_tokens+=r['n'] if flag else 0
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,unsupported_errors=unsupported_errors,supported=sum(r['supported'] for r in records),n=len(records),flagged_tokens=flagged_tokens,flagged_types=[r['anchor_id'] for r in records if flagged(r,threshold)])


def choose_threshold(clean,corrupted):
    curve=[];clean_tokens=sum(r['n'] for r in clean)
    for threshold in THRESHOLDS:
        c=metrics(clean,threshold);e=metrics(corrupted,threshold)
        eligible=c['fp']<=1 and c['flagged_tokens']<=.05*clean_tokens
        curve.append(dict(threshold=None if math.isinf(threshold) else threshold,clean=c,corrupted=e,eligible=eligible))
    selected=max((r for r in curve if r['eligible']),key=lambda r:(r['corrupted']['tp'],-r['corrupted']['fp'],-r['clean']['flagged_tokens'],float('inf') if r['threshold'] is None else r['threshold']))
    return selected,curve
