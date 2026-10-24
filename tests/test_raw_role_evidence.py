from copy import deepcopy
import math
import numpy as np
from voynich_smt.raw_role_evidence import evidence
from voynich_smt.dependency_role_proxy import evidence as normalized_evidence,pos_prior,infer,calibrate


def test_raw_values_match_non_dependent_and_carrier_role_logs():
    p=np.asarray([[.1,.2,.3,.4],[.8,.1,.05,.05],[.05,.6,.25,.1]])
    options=[(2,'direct'),(1,'cop'),(1,'aux')];original=deepcopy(options)
    head,typ=evidence(2,options,p)
    assert np.allclose(head,np.log([.95,.2,.2]))
    assert np.allclose(typ,np.log([.1,.6,.25]))
    assert options==original


def test_prior_subtraction_is_the_only_difference():
    tokens=[dict(pos='NOUN'),dict(pos='ADJ'),dict(pos='AUX')]
    model=dict(pos_counts={p:{'dependent':2,'cop':1,'aux':1,'other':6} for p in ('NOUN','ADJ','AUX')})
    p=np.asarray([pos_prior(model,t['pos']) for t in tokens]);options=[(2,'direct'),(1,'cop'),(1,'aux')]
    normalized=normalized_evidence(tokens,2,options,p,model);raw=evidence(2,options,p)
    assert np.allclose(normalized[0],0) and np.allclose(normalized[1],0)
    assert np.all(raw[0]<0) and np.all(raw[1]<0)
    assert infer(np.asarray([2.,1.,0.]),options,0,2,*raw,0,0)==[0,2,2,'direct']


def test_zero_probabilities_are_clipped_not_deleted():
    p=np.asarray([[1.,0.,0.,0.],[0.,0.,0.,1.]])
    options=[(0,'cop'),(0,'aux'),(1,'direct')]
    head,typ=evidence(1,options,p)
    assert np.isfinite(head).all() and np.isfinite(typ).all()
    assert head[0]==math.log(1e-6) and typ[0]==math.log(1e-6)
    assert len(head)==len(options)==3


def test_soft_raw_type_evidence_can_recover_a_lower_scoring_correct_type():
    options=[(2,'direct'),(1,'cop')];p=np.asarray([[.1,.3,.3,.3],[.1,.3,.3,.3],[0.,.9,.09,.01]])
    head,typ=evidence(2,options,p);frame=dict(scores=np.asarray([1.,0.]),options=options,gold=[0,1,2,'cop'],head=head,type=typ)
    selected=calibrate([frame],'type')['selected']
    assert selected['head_weight']==0 and selected['type_weight']==.5 and selected['correct']==1
