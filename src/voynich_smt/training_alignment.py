"""Source cross-fitting and graph-contrast training utilities."""
from collections import defaultdict
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import minimize,linprog

from .parent_ranking import ConditionalRanker


def blocked_folds(author_by_stream,folds=4):
    if folds<2:raise ValueError('At least two folds required')
    groups=defaultdict(list)
    for i,author in enumerate(author_by_stream):groups[author].append(i)
    assignments=[None]*len(author_by_stream)
    for indices in groups.values():
        width=math.ceil(len(indices)/folds)
        for rank,index in enumerate(indices):assignments[index]=min(folds-1,rank//width)
    return assignments


def fit_graph_contrast(initial,differences,regularization=.01):
    """Pairwise logistic ranking anchored to a conditional source model.

    Differences are already standardized and normalized per predicate. No
    validation example or feature-scaler refit enters this function.
    """
    d=np.asarray(differences,dtype=float)
    if d.ndim!=2 or len(d)==0 or d.shape[1]!=len(initial.weights)-1:
        raise ValueError('Nonempty matching feature differences required')
    anchor=np.asarray(initial.weights[1:]);reg=regularization
    def objective(w):
        margin=d@w;probability=1/(1+np.exp(np.clip(margin,-40,40)))
        delta=w-anchor
        loss=np.mean(np.logaddexp(0,-margin))+reg*np.dot(delta,delta)/2
        gradient=-d.T@probability/len(d)+reg*delta
        return loss,gradient
    result=minimize(objective,anchor,jac=True,method='L-BFGS-B',options={'maxiter':300})
    if not result.success:raise ValueError('Graph-contrast training did not converge: '+result.message)
    return ConditionalRanker([0.]+result.x.tolist(),list(initial.mean),list(initial.scale))


def separability_audit(differences):
    """Numerical feasibility of unit-margin fitting constraints, never inference."""
    d=np.asarray(differences,dtype=float)
    if d.ndim!=2 or len(d)==0:return {'status':'not_applicable','constraints':0}
    result=linprog(np.zeros(d.shape[1]),A_ub=-d,b_ub=-np.ones(len(d)),bounds=[(None,None)]*d.shape[1],method='highs')
    return {'status':'feasible' if result.success else 'infeasible' if result.status==2 else 'unresolved',
        'constraints':len(d),'solver_status':int(result.status),'message':result.message,
        'minimum_margin':float(np.min(d@result.x)) if result.success else None,
        'scope':'numerical fitting-only feasibility; not a proof certificate or held-out generalization result'}
