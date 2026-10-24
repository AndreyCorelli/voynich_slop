from copy import deepcopy
import numpy as np
from scipy.sparse import csr_matrix
from voynich_smt.dependency_role_proxy import features,label,objective,probabilities,fit,pos_prior,evidence,infer,calibrate


def tokens():
    return [dict(word='res',pos='NOUN',head=1,rel='nsubj',features={'Case':'Nom'}),dict(word='bona',pos='ADJ',head=None,rel='root',features={}),dict(word='est',pos='AUX',head=1,rel='cop',features={'VerbForm':'Fin'})]


def test_role_features_ignore_annotations_and_lexical_scope_is_explicit():
    ts=tokens();masked=[dict(t,head=None,rel='?',features={},lemma='?') for t in ts]
    for mode in ('pos','lexical'):
        assert [features(ts,i,mode) for i in range(3)]==[features(masked,i,mode) for i in range(3)]
    altered=deepcopy(ts);altered[1]['word']='alia'
    assert features(ts,1,'pos')==features(altered,1,'pos')
    assert features(ts,1,'lexical')!=features(altered,1,'lexical')
    assert [label(dict(rel=r)) for r in ('amod','nmod:poss','cop','aux','acl:relcl')]==['dependent','dependent','cop','aux','other']


def test_multiclass_gradient_matches_finite_differences():
    x=csr_matrix([[1.,0.],[1.,2.],[1.,-1.]])
    y=np.asarray([0,2,3]);w=np.linspace(-.2,.3,8);_,gradient=objective(w,x,y)
    for i in range(len(w)):
        delta=np.zeros_like(w);delta[i]=1e-6
        numeric=(objective(w+delta,x,y)[0]-objective(w-delta,x,y)[0])/2e-6
        assert abs(numeric-gradient[i])<1e-7


def test_pos_prior_normalization_and_zero_weights_preserve_scores():
    ts=tokens();model=dict(pos_counts={p:{'dependent':2,'cop':1,'aux':1,'other':6} for p in ('NOUN','ADJ','AUX')});p=np.asarray([pos_prior(model,t['pos']) for t in ts]);options=[(2,'direct'),(1,'cop'),(1,'aux')];head,typ=evidence(ts,2,options,p,model)
    assert np.allclose(head,0) and np.allclose(typ,0)
    assert infer(np.asarray([0.,2.,1.]),options,0,2,np.ones(3),np.ones(3),0,0)==[0,1,2,'cop']


def test_calibration_prefers_zero_when_new_evidence_adds_nothing():
    frame=dict(scores=np.asarray([2.,1.]),options=[(2,'direct'),(1,'cop')],gold=[0,2,2,'direct'],head=np.ones(2),type=np.ones(2))
    for arm in ('head','type','joint'):
        chosen=calibrate([frame],arm)['selected']
        assert chosen['head_weight']==chosen['type_weight']==0


def test_fit_probability_normalization_and_inference_nonmutation():
    ts=tokens();model=fit([ts]*5,'lexical');original=deepcopy(model);masked=[dict(t,head=None,rel='?',features={}) for t in ts];p=probabilities(ts,model)
    assert p.shape==(3,4) and np.allclose(p.sum(axis=1),1)
    assert np.array_equal(p,probabilities(masked,model))
    assert model==original
