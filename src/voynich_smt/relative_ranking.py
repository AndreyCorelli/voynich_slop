"""Pairwise passage ranking: no reference-dependent intercept or centering."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


def fit_ranker(differences, weights, ridge, nonnegative=True):
    x=np.asarray(differences,dtype=float);sample=np.asarray(weights,dtype=float)
    if x.ndim!=2 or len(x)==0 or sample.shape!=(len(x),) or np.any(sample<=0) or ridge<=0:
        raise ValueError('Nonempty pair matrix, positive weights and ridge required')
    sample=sample/sample.sum()
    def objective(w):
        margin=x@w
        return float(sample@np.logaddexp(0,-margin)+.5*ridge*(w@w)),x.T@(-sample*expit(-margin))+ridge*w
    result=minimize(objective,np.zeros(x.shape[1]),jac=True,bounds=[(0,None) if nonnegative else (None,None)]*x.shape[1],method='L-BFGS-B',options={'maxiter':2000,'ftol':1e-12})
    if not result.success:raise ValueError(result.message)
    return result.x


def pair_weights(pairs):
    # Equal mass per work, then width, then comparison kind; repeated variants
    # do not grant larger works or densely sampled cells extra fitting mass.
    from collections import Counter
    counts=Counter((p['document'],str(p['width']),p['kind']) for p in pairs)
    widths={doc:{str(p['width']) for p in pairs if p['document']==doc} for doc,_,_ in counts}
    kinds={(doc,width):{p['kind'] for p in pairs if p['document']==doc and str(p['width'])==width} for doc,width,_ in counts}
    return np.asarray([1/(len(widths[p['document']])*len(kinds[p['document'],str(p['width'])])*counts[p['document'],str(p['width']),p['kind']]) for p in pairs])
