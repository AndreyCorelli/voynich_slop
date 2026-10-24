"""Relative conjunct evidence only where original subjects contest a carrier."""
from collections import defaultdict
import math
from voynich_smt.joint_subject_none import independent
from voynich_smt.conj_subject_evidence import probabilities


def adjust_contests(frames,tokens,model,weight,cutoff):
    if weight<0:raise ValueError('Evidence weight must be nonnegative')
    if weight==0:return [dict(r) for r in frames]
    original,_=independent(frames,cutoff);groups=defaultdict(list)
    for s,v in original.items():
        if v is not None:groups[v].append(s)
    groups={v:ss for v,ss in groups.items() if len(ss)>1}
    if not groups:return [dict(r) for r in frames]
    p=probabilities(tokens,[r['subject'] for r in frames],model);logq={r['subject']:math.log(max(1e-6,1-float(q))) for r,q in zip(frames,p)};references={v:max(logq[s] for s in ss) for v,ss in groups.items()};result=[]
    for r in frames:
        other=dict(r)
        if original[r['subject']] is None:
            # Preserve original best-tie / below-cutoff abstention eligibility.
            other.update(predicates=[],scores=[])
        else:
            other['scores']=[score+weight*min(0.,logq[r['subject']]-references[v]) if v in references else score for v,score in zip(r['predicates'],r['scores'])]
        result.append(other)
    return result
