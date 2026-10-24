"""Per-token finite-subject attachment with a learned NONE alternative."""
import math
import numpy as np
from scipy.optimize import minimize
from voynich_smt.link_ranking import features as boundary_features

POS=('ADJ','ADP','ADV','AUX','CCONJ','DET','INTJ','NOUN','NUM','PRON','PROPN','SCONJ','VERB','BOUNDARY')
STRUCTURAL=('edge_bias','log_distance','subject_before','log_verbal_between','log_subordinator_between','log_coordinator_between','subject_pronoun','subject_proper')
LOCAL=tuple(f'{endpoint}_{side}_{pos}' for endpoint in ('subject','predicate') for side in ('previous','next') for pos in POS)
MORPH=('subject_log_role_odds','predicate_log_role_odds','log_number_agreement','log_person_agreement')
FEATURES={'structural':STRUCTURAL,'local_morph':STRUCTURAL+LOCAL+MORPH}
THRESHOLDS=(0.,.1,.2,.3,.4,.5,.6,.7,.8,.85,.9,.95,.975,.99,1.1)
DISTANCES=(0,1,2,3,4,6,8,12,16,24,32,64,1000000)


def vector(tokens,subject,predicate,probabilities,arm):
    f=boundary_features(tokens,subject,predicate)
    values=[1.,math.log1p(f['distance']),float(subject<predicate),math.log1p(f['verbal']),math.log1p(f['subordinator']),math.log1p(f['coordinator']),float(tokens[subject]['pos']=='PRON'),float(tokens[subject]['pos']=='PROPN')]
    if arm=='structural':return values
    if arm!='local_morph':raise ValueError(arm)
    for index in (subject,predicate):
        for neighbor in (index-1,index+1):
            pos=tokens[neighbor]['pos'] if 0<=neighbor<len(tokens) else 'BOUNDARY'
            values.extend(float(pos==p) for p in POS)
    a,b=probabilities[subject],probabilities[predicate]
    for p in (a['role'][1],b['role'][1]):
        p=min(1-1e-6,max(1e-6,p));values.append(math.log(p/(1-p)))
    for feature in ('number','person'):
        values.append(math.log(max(1e-6,sum(x*y for x,y in zip(a[feature],b[feature])))))
    return values


def objective(weights,x,starts,targets,regularization=.01):
    scores=x@weights
    maxima=np.maximum.reduceat(scores,starts)
    lengths=np.diff(np.append(starts,len(scores)))
    exp=np.exp(scores-np.repeat(maxima,lengths));sums=np.add.reduceat(exp,starts)
    loss=np.mean(np.log(sums)+maxima-scores[targets])+.5*regularization*float(weights@weights)
    residual=exp/np.repeat(sums,lengths);residual[targets]-=1
    gradient=x.T@residual/len(starts)+regularization*weights
    return float(loss),gradient


def fit(frames,arm):
    rows=[];starts=[];targets=[];omitted=0;positives=0
    for frame in frames:
        gold=frame['gold'];predicates=frame['predicates']
        if gold is not None and gold not in predicates:omitted+=1;continue
        starts.append(len(rows));targets.append(len(rows)+(predicates.index(gold)+1 if gold is not None else 0));positives+=gold is not None
        rows.append([0.]*len(FEATURES[arm]));rows.extend(frame['vectors'][arm])
    x=np.asarray(rows,dtype=float);starts=np.asarray(starts);targets=np.asarray(targets)
    result=minimize(objective,np.zeros(x.shape[1]),args=(x,starts,targets),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-10,gtol=1e-6))
    assert result.success,result.message
    return dict(arm=arm,weights=result.x.tolist(),features=FEATURES[arm],training_frames=len(starts),positive_frames=positives,omitted_unrepresentable=omitted,loss=float(result.fun),iterations=int(result.nit),regularization=.01)


def propose(frame,model):
    if not frame['predicates']:return dict(predicate=None,confidence=1.)
    scores=np.asarray([0.]+(np.asarray(frame['vectors'][model['arm']])@np.asarray(model['weights'])).tolist())
    winners=np.flatnonzero(np.isclose(scores,scores.max(),rtol=0,atol=1e-10));mass=np.exp(scores-scores.max());mass/=mass.sum()
    # A tie or winning NONE is an abstention, not an index-based attachment.
    index=int(winners[0]) if len(winners)==1 else 0
    return dict(predicate=frame['predicates'][index-1] if index else None,confidence=float(mass[index]))


def distance_proposal(frame):
    if not frame['predicates']:return dict(predicate=None,confidence=0.)
    distances=[abs(frame['subject']-v) for v in frame['predicates']];minimum=min(distances)
    return dict(predicate=frame['predicates'][distances.index(minimum)] if distances.count(minimum)==1 else None,confidence=float(minimum))


def edge_metrics(gold,predicted):
    tp=len(gold&predicted);fp=len(predicted-gold);fn=len(gold-predicted)
    return dict(tp=tp,fp=fp,fn=fn,predicted=len(predicted),gold=len(gold),precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.)


def accept(proposal,threshold,distance=False):
    return proposal['predicate'] is not None and (proposal['confidence']<=threshold if distance else proposal['confidence']>=threshold)


def calibrate(frames,proposals,distance=False):
    gold={(f['sid'],f['subject'],f['gold']) for f in frames if f['gold'] is not None};records=[]
    for threshold in DISTANCES if distance else THRESHOLDS:
        predictions={(f['sid'],f['subject'],p['predicate']) for f,p in zip(frames,proposals) if accept(p,threshold,distance)}
        records.append(dict(threshold=threshold,**edge_metrics(gold,predictions)))
    # F1 ties favor fewer predictions. High-precision target is empirical, not a guarantee.
    f1=max(records,key=lambda r:(r['f1'],-r['predicted']))
    eligible=[r for r in records if r['predicted']>=20 and r['precision'] is not None and r['precision']>=.9]
    high=max(eligible,key=lambda r:(r['tp'],-r['fp'])) if eligible else dict(threshold=-1 if distance else 1.1,predicted=0,note='No threshold met calibration precision90 with20 predictions')
    return dict(f1=f1,precision90=high,grid=records)
