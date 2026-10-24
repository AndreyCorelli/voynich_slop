"""Frame-normalized pairwise head/type ranking with fixed training-only opponents."""
from collections import Counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from voynich_smt.typed_predicate_units import FEATURES


def pairs(frames,mode,baseline_weights):
    if mode not in ('pair_all','pair_hard'):raise ValueError(mode)
    differences=[];weights=[];counts=Counter();n=len(frames)
    for r in frames:
        gold=r['options'].index(tuple(r['gold'][1::2]));wrong=[j for j in range(len(r['options'])) if j!=gold]
        if not wrong:continue
        if mode=='pair_hard':
            scores=r['x']@np.asarray(baseline_weights)
            # All tied strongest wrong opponents receive equal mass; gold is never selected.
            best=max(scores[j] for j in wrong)
            wrong=[j for j in wrong if np.isclose(scores[j],best,rtol=0,atol=1e-10)]
        for j in wrong:
            differences.append(r['x'][gold]-r['x'][j]);weights.append(1/(n*len(wrong)))
            counts[r['gold'][3]+'->'+r['options'][j][1]]+=1
    if not differences:raise ValueError('No competing candidates')
    return np.asarray(differences),np.asarray(weights),dict(counts)


def objective(w,differences,pair_weights,regularization=.01):
    margins=differences@w
    loss=float(pair_weights@np.logaddexp(0.,-margins))+.5*regularization*float(w@w)
    gradient=differences.T@(-pair_weights*expit(-margins))+regularization*w
    return loss,gradient


def fit(frames,mode,baseline_weights):
    differences,weights,counts=pairs(frames,mode,baseline_weights)
    result=minimize(objective,np.zeros(len(FEATURES)),args=(differences,weights),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-10,gtol=1e-6))
    assert result.success,result.message
    return dict(weights=result.x.tolist(),features=FEATURES,mode=mode,training_frames=len(frames),pairs=len(weights),pair_mass=float(weights.sum()),pair_counts=counts,regularization=.01,loss=float(result.fun),iterations=int(result.nit))
