"""Calibrated linear combinations of sentence proxies, with grouped evaluation."""
from collections import defaultdict
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

def fit_linear(features,labels,regularization,nonnegative=True):
    x=np.asarray(features,dtype=float);y=np.asarray(labels,dtype=float)
    sample=np.where(y==1,.5/max(1,sum(y==1)),.5/max(1,sum(y==0)))
    def objective(parameters):
        w,b=parameters[:-1],parameters[-1];z=x@w+b
        value=np.sum(sample*(np.logaddexp(0,z)-y*z))+.5*regularization*(w@w)
        error=sample*(expit(z)-y)
        return value,np.r_[x.T@error+regularization*w,error.sum()]
    bounds=[(0,None) if nonnegative else (None,None)]*x.shape[1]+[(None,None)]
    result=minimize(objective,np.zeros(x.shape[1]+1),jac=True,bounds=bounds,method='L-BFGS-B',options={'maxiter':2000,'ftol':1e-12})
    if not result.success:raise ValueError(result.message)
    return result.x

def threshold(scores,labels):
    values=np.unique(scores)
    candidates=np.r_[values[0]-1,(values[:-1]+values[1:])/2,values[-1]+1]
    y=np.asarray(labels,dtype=bool)
    def balanced(t):
        pred=scores>=t
        return .5*(np.mean(pred[y])+np.mean(~pred[~y]))
    chosen=max(candidates,key=lambda t:(balanced(t),-abs(t)))
    return float(chosen)

def evaluate(rows,scores,cutoff):
    y=np.asarray([r['valid'] for r in rows],dtype=bool);pred=np.asarray(scores)>=cutoff
    by_family={}
    for family in sorted({r['family'] for r in rows}):
        indices=np.asarray([i for i,r in enumerate(rows) if r['family']==family])
        by_family[family]={'cases':len(indices),'accuracy':float(np.mean(pred[indices]==y[indices])),
            'accepted':int(pred[indices].sum())}
    originals={r['base']:float(score) for r,score in zip(rows,scores) if r['family']=='original'}
    pairs=[originals[r['base']]>score+1e-10 for r,score in zip(rows,scores) if not r['valid']]
    return {'cases':len(rows),'valid_acceptance':float(np.mean(pred[y])),'corrupt_rejection':float(np.mean(~pred[~y])),
        'balanced_accuracy':float(.5*(np.mean(pred[y])+np.mean(~pred[~y]))),'paired_accuracy':float(np.mean(pairs)),
        'negative_pairs':len(pairs),'families':by_family}

def grouped_intervals(rows,scores,cutoff,iterations=1000,seed=1207):
    groups=defaultdict(list)
    for i,row in enumerate(rows):groups[row['base']].append(i)
    names=sorted(groups);rng=np.random.default_rng(seed);records=[]
    for _ in range(iterations):
        chosen=rng.choice(names,len(names),replace=True);indices=[i for name in chosen for i in groups[name]]
        sampled=[{**rows[i],'base':f'{copy}-{rows[i]["base"]}'} for copy,name in enumerate(chosen) for i in groups[name]]
        metrics=evaluate(sampled,np.asarray(scores)[indices],cutoff)
        records.append([metrics['balanced_accuracy'],metrics['paired_accuracy']])
    values=np.asarray(records)
    return {key:[float(x) for x in np.quantile(values[:,i],[.025,.975])] for i,key in enumerate(('balanced_accuracy','paired_accuracy'))}
