import numpy as np
from voynich_smt.multi_link_attachment import objective,vector,fit,propose,distance_proposal,calibrate,accept,edge_metrics


def test_conditional_softmax_gradient_matches_numeric_derivative():
    x=np.asarray([[0.,0.],[1.,2.],[1.,-1.],[0.,0.],[1.,3.]])
    starts=np.array([0,3]);targets=np.array([2,3]);w=np.array([.2,-.3]);loss,gradient=objective(w,x,starts,targets)
    for i in range(2):
        delta=np.zeros(2);delta[i]=1e-6
        numeric=(objective(w+delta,x,starts,targets)[0]-objective(w-delta,x,starts,targets)[0])/2e-6
        assert abs(gradient[i]-numeric)<1e-7
    assert np.isfinite(loss)


def test_features_ignore_gold_edges_and_morphology_annotations():
    tokens=[dict(pos=p,features={'Case':'Nom'},head=0,rel='nsubj') for p in ('ADP','NOUN','VERB')]
    masked=[dict(t,head=None,rel='?',features={}) for t in tokens]
    probs={i:dict(role=[.2,.8],number=[.7,.3],person=[0.,0.,1.]) for i in (1,2)}
    for arm in ('structural','local_morph'):assert vector(tokens,1,2,probs,arm)==vector(masked,1,2,probs,arm)


def test_none_winner_and_ties_abstain():
    model=dict(arm='structural',weights=[-1.])
    frame=dict(subject=0,predicates=[1,2],vectors={'structural':[[1.],[1.]]})
    assert propose(frame,model)['predicate'] is None
    assert propose(frame,dict(model,weights=[0.]))['predicate'] is None
    assert distance_proposal(dict(frame,subject=1,predicates=[0,2]))['predicate'] is None
    assert not accept(dict(predicate=None,confidence=1),0)


def test_unrepresentable_positive_not_trained_as_none():
    frames=[dict(gold=None,predicates=[],vectors={'structural':[]}),dict(gold=3,predicates=[],vectors={'structural':[]})]
    model=fit(frames,'structural')
    assert model['omitted_unrepresentable']==1 and model['training_frames']==1
    assert model['positive_frames']==0


def test_metrics_count_wrong_attachment_as_fp_and_fn():
    m=edge_metrics({('s',1,3),('s',2,3)},{('s',1,4),('s',2,3)})
    assert (m['tp'],m['fp'],m['fn'])==(1,1,1)
    assert m['precision']==m['recall']==m['f1']==.5


def test_precision_target_can_fail_without_forcing_prediction():
    frames=[dict(sid='s',subject=0,gold=None)]
    policies=calibrate(frames,[dict(predicate=1,confidence=.8)])
    assert policies['precision90']['threshold']==1.1
    assert not accept(dict(predicate=1,confidence=.99),policies['precision90']['threshold'])
