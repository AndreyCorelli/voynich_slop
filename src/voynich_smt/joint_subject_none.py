"""Soft carrier competition with optional subject attachment and no hard cap."""
from collections import Counter
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

PENALTIES=(0.,.25,.5,1.,2.,4.,8.)


def independent(frames,cutoff):
    predictions={r['subject']:None for r in frames};eligible=[]
    for r in frames:
        if not r['predicates']:continue
        scores=np.asarray(r['scores']);best=float(scores.max());winners=np.flatnonzero(np.isclose(scores,best,rtol=0,atol=1e-10))
        # Preserve original abstention on tied best edges, including in joint arms.
        if len(winners)!=1 or best<=cutoff+1e-10:continue
        predictions[r['subject']]=r['predicates'][int(winners[0])]
        for j,v in enumerate(r['predicates']):
            utility=float(scores[j]-cutoff)
            if utility>1e-10:eligible.append((r['subject'],v,utility))
    return predictions,eligible


def decode(frames,cutoff,penalty):
    if penalty<0:raise ValueError('Competition penalty must be nonnegative')
    predictions,edges=independent(frames,cutoff);counts=Counter(v for v in predictions.values() if v is not None);stats=dict(solved=0,ambiguous_subjects=0,alternative_solves=0)
    if penalty==0 or not any(n>1 for n in counts.values()):return predictions,stats
    subjects=sorted({s for s,_,_ in edges});carriers=sorted({v for _,v,_ in edges});si={s:j for j,s in enumerate(subjects)};vi={v:len(subjects)+j for j,v in enumerate(carriers)};n=len(edges)
    # x_e attaches a subject; y_v consumes the first free slot at carrier v.
    # Each extra attachment costs penalty; NONE has utility0. This network LP
    # has integral vertices (signed incidence matrix and integral bounds).
    a=lil_matrix((len(subjects)+len(carriers),n+len(carriers)),dtype=float)
    for j,(s,v,_) in enumerate(edges):a[si[s],j]=1.;a[vi[v],j]=-1.
    for j,v in enumerate(carriers):a[vi[v],n+j]=1.
    b=np.asarray([1.]*len(subjects)+[0.]*len(carriers));cost=np.asarray([penalty-u for _,_,u in edges]+[-penalty]*len(carriers));bounds=[(0.,1.)]*len(cost);a=a.tocsr()
    def solve(bound):
        result=linprog(cost,A_ub=a,b_ub=b,bounds=bound,method='highs-ds',options=dict(primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
        assert result.success,result.message
        assert np.max(np.abs(result.x-np.round(result.x)))<1e-6,'Network LP returned fractional vertex'
        return result
    result=solve(bounds);stats['solved']=1;predictions={r['subject']:None for r in frames}
    for j,(s,v,_) in enumerate(edges):
        if result.x[j]<.5:continue
        other=list(bounds);other[j]=(0.,0.);alternative=solve(other);stats['alternative_solves']+=1
        # Emit an attachment only if it occurs in every optimum.
        if abs(alternative.fun-result.fun)<=1e-8:stats['ambiguous_subjects']+=1
        else:predictions[s]=v
    return predictions,stats
