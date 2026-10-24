"""Source-only nested text sizes and constant candidate/error availability."""
from collections import Counter,defaultdict
from voynich_smt.paired_anchor_class import recommend


def supported_words(sentences,words):
    n=Counter();sids=defaultdict(set)
    for s in sentences:
        for t in s['tokens']:
            if t['word'] in words:n[t['word']]+=1;sids[t['word']].add(s['sent_id'])
    return {w for w in words if n[w]>=5 and len(sids[w])>=3}


def length_blocks(previous):
    hundred=[previous['scored']['sparse'+str(i)] for i in range(8)];result={}
    for n in (100,200,400,800):
        width=n//100
        for i in range(8//width):result[str(n)+'-'+str(i)]=sum(hundred[i*width:(i+1)*width],[])
    result['829-0']=previous['scored']['full'];return result


def curve_metrics(scores,reference,threshold):
    selected=recommend(scores,threshold);hit=selected is not None and reference['pair'] is not None and selected==reference['pair'];rank1=recommend(scores,float('-inf'));error=reference['error']
    return dict(error=error,hit=int(hit),wrong=int(selected is not None and not hit),abstain=selected is None,reference_supported=any(r['supported'] and r['pair']==reference['pair'] for r in scores),rank1_correct=int(error and rank1 is not None and rank1==reference['pair']),selected=selected)


def aggregate(rows):
    errors=[r for r in rows if r['error']];hit=sum(r['hit'] for r in errors);wrong=sum(r['wrong'] for r in errors);calls=hit+wrong
    return dict(error_cases=len(errors),hit=hit,wrong=wrong,abstain=sum(r['abstain'] for r in errors),precision=hit/calls if calls else None,recall=hit/len(errors) if errors else None,reference_supported=sum(r['reference_supported'] for r in errors),rank1_correct=sum(r['rank1_correct'] for r in errors),control_cases=len(rows)-len(errors),control_false=sum(r['wrong'] for r in rows if not r['error']))
