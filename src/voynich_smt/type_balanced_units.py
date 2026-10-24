"""Type-balanced conditional unit loss and matched calibration of role biases."""
from collections import Counter
import numpy as np
from scipy.optimize import minimize
from voynich_smt.typed_predicate_units import FEATURES,ROLES,select

OFFSETS=(-2.,-1.,-.5,0.,.5,1.,2.)


def objective(weights,x,starts,targets,frame_weights,regularization=.01):
    assert np.isfinite(frame_weights).all() and np.all(frame_weights>0)
    scores=x@weights;maximum=np.maximum.reduceat(scores,starts);lengths=np.diff(np.append(starts,len(scores)));exp=np.exp(scores-np.repeat(maximum,lengths));sums=np.add.reduceat(exp,starts);scale=frame_weights/frame_weights.sum()
    loss=float(scale@(np.log(sums)+maximum-scores[targets]))+.5*regularization*float(weights@weights)
    residual=exp/np.repeat(sums,lengths);residual[targets]-=1;residual*=np.repeat(scale,lengths)
    return loss,x.T@residual+regularization*weights


def fit(frames,balanced=True):
    counts=Counter(r['gold'][3] for r in frames);n=len(frames);class_weights={role:n/(len(counts)*count) if balanced else 1. for role,count in counts.items()};frame_weights=np.asarray([class_weights[r['gold'][3]] for r in frames]);x=np.concatenate([r['x'] for r in frames]);starts=np.cumsum([0]+[len(r['options']) for r in frames[:-1]]);targets=np.asarray([start+r['options'].index(tuple(r['gold'][1::2])) for start,r in zip(starts,frames)])
    result=minimize(objective,np.zeros(len(FEATURES)),args=(x,starts,targets,frame_weights),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-10,gtol=1e-6));assert result.success,result.message
    return dict(weights=result.x.tolist(),features=FEATURES,balanced=balanced,type_counts=dict(counts),class_weights=class_weights,training_frames=n,regularization=.01,loss=float(result.fun),iterations=int(result.nit))


def infer(scores,options,subject,carrier,offsets):
    return select(scores+np.asarray([offsets[role] for _,role in options]),options,subject,carrier)


def calibrate(frames,objective_name):
    if objective_name not in ('micro','macro'):raise ValueError(objective_name)
    totals=Counter(r['gold'][3] for r in frames);records=[]
    for cop in OFFSETS:
        for aux in OFFSETS:
            offsets=dict(direct=0.,cop=cop,aux=aux);correct=Counter()
            for r in frames:
                if infer(r['scores'],r['options'],r['gold'][0],r['gold'][2],offsets)==r['gold']:correct[r['gold'][3]]+=1
            macro=float(np.mean([correct[role]/total for role,total in totals.items()])) if totals else 0.
            records.append(dict(offsets=offsets,correct=sum(correct.values()),n=len(frames),macro_recall=macro,per_type={role:dict(correct=correct[role],n=total) for role,total in totals.items()}))
    key='correct' if objective_name=='micro' else 'macro_recall'
    chosen=max(records,key=lambda r:(r[key],-sum(abs(v) for v in r['offsets'].values())))
    return dict(objective=objective_name,selected=chosen,grid=records)
