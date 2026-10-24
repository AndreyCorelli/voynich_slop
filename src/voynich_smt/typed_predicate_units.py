"""POS/position-only head/type inference; annotation targets are separate."""
import math
from collections import Counter,defaultdict
import numpy as np
from scipy.optimize import minimize
from voynich_smt.multi_link_attachment import POS,objective
from voynich_smt.link_ranking import features as boundary_features
from voynich_smt.predicate_carriers import target

ROLES=('direct','cop','aux')
DISTANCES=(0.,.5,1.,2.,4.)
BASE_FEATURES=('bias','log_head_carrier_distance','log_head_subject_distance','head_before_carrier','head_between_subject_carrier')+tuple('headPOS_'+p for p in POS)+('carrier_VERB','carrier_AUX','log_verbal_between','log_sconj_between','log_cconj_between','subject_NOUN','subject_PROPN','subject_PRON','head_prev_ADP','head_next_ADP','head_prev_SCONJ','head_next_SCONJ','adjacent_carrier')
FEATURES=tuple(role+'/'+name for role in ROLES for name in BASE_FEATURES)


def gold_unit(tokens,subject):
    truth=target(tokens,subject)
    if truth['ambiguous'] or truth['carrier'] is None:return None
    carrier=truth['carrier'];head=carrier if truth['kind']=='direct' else tokens[subject]['head'];role='direct' if truth['kind']=='direct' else 'cop' if truth['kind']=='copula' else 'aux'
    return [subject,head,carrier,role]


def choices(tokens,subject,carrier):
    return [(carrier,'direct')]+[(h,role) for h in range(len(tokens)) if h not in (subject,carrier) for role in ('cop','aux')]


def matrix(tokens,subject,carrier,options):
    result=np.zeros((len(options),len(FEATURES)));width=len(BASE_FEATURES)
    for j,(head,role) in enumerate(options):
        f=boundary_features(tokens,head,carrier);values=[1.,math.log1p(abs(head-carrier)),math.log1p(abs(head-subject)),float(head<carrier),float(min(subject,carrier)<head<max(subject,carrier))]
        values.extend(float(tokens[head]['pos']==p) for p in POS);values.extend(float(tokens[carrier]['pos']==p) for p in ('VERB','AUX'));values.extend(math.log1p(f[p]) for p in ('verbal','subordinator','coordinator'));values.extend(float(tokens[subject]['pos']==p) for p in ('NOUN','PROPN','PRON'))
        for p in ('ADP','SCONJ'):
            for neighbor in (head-1,head+1):values.append(float(0<=neighbor<len(tokens) and tokens[neighbor]['pos']==p))
        values.append(float(abs(head-carrier)==1));offset=ROLES.index(role)*width;result[j,offset:offset+width]=values
    return result


def fit(frames):
    x=np.concatenate([r['x'] for r in frames]);starts=np.cumsum([0]+[len(r['options']) for r in frames[:-1]]);targets=np.asarray([start+r['options'].index(tuple(r['gold'][1::2])) for start,r in zip(starts,frames)])
    # gold[1::2] = (head, role); no NONE choice because endpoints are conditioned on.
    result=minimize(objective,np.zeros(len(FEATURES)),args=(x,starts,targets),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-10,gtol=1e-6))
    assert result.success,result.message
    type_counts=defaultdict(Counter);head_counts=defaultdict(Counter)
    for r in frames:
        s,h,v,role=r['gold'];type_counts[r['carrier_pos']][role]+=1;head_counts[role][r['head_pos']]+=1
    return dict(weights=result.x.tolist(),features=FEATURES,regularization=.01,training_frames=len(frames),loss=float(result.fun),iterations=int(result.nit),type_counts={k:dict(v) for k,v in type_counts.items()},head_pos_counts={k:dict(v) for k,v in head_counts.items()})


def prior_scores(tokens,carrier,options,model,weight):
    types=model['type_counts'].get(tokens[carrier]['pos'],{});n=sum(types.values());scores=[]
    for head,role in options:
        counts=model['head_pos_counts'].get(role,{});m=sum(counts.values());p=(types.get(role,0)+.5)/(n+.5*len(ROLES));q=(counts.get(tokens[head]['pos'],0)+.5)/(m+.5*len(POS));scores.append(math.log(p)+math.log(q)-weight*math.log1p(abs(head-carrier)))
    return np.asarray(scores)


def select(scores,options,subject,carrier):
    winners=np.flatnonzero(np.isclose(scores,scores.max(),rtol=0,atol=1e-10))
    if len(winners)!=1:return None
    head,role=options[int(winners[0])];return [subject,head,carrier,role]


def infer(tokens,subject,carrier,model,weight=None):
    options=choices(tokens,subject,carrier)
    scores=matrix(tokens,subject,carrier,options)@np.asarray(model['weights']) if weight is None else prior_scores(tokens,carrier,options,model,weight)
    return select(scores,options,subject,carrier)


def calibrate_distance(frames,tokens_by_id,model):
    records=[]
    for weight in DISTANCES:
        correct=0
        for r in frames:
            scores=prior_scores(tokens_by_id[r['sid']],r['gold'][2],r['options'],model,weight);correct+=select(scores,r['options'],r['gold'][0],r['gold'][2])==r['gold']
        records.append(dict(weight=weight,correct=correct,n=len(frames)))
    return dict(selected=max(records,key=lambda r:r['correct']),grid=records)
