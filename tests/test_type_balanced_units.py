import numpy as np
from voynich_smt.type_balanced_units import objective,fit,infer,calibrate
from voynich_smt.multi_link_attachment import objective as original_objective
from voynich_smt.typed_predicate_units import FEATURES,select


def sample():
    return np.asarray([[1.,0.],[0.,1.],[1.,1.],[2.,1.],[1.,-1.]]),np.asarray([0,3]),np.asarray([1,4]),np.asarray([.2,-.3])


def test_unit_weights_reproduce_original_objective_and_gradient():
    x,starts,targets,w=sample();loss,g=objective(w,x,starts,targets,np.ones(2));old,og=original_objective(w,x,starts,targets)
    assert abs(loss-old)<1e-12 and np.allclose(g,og,atol=1e-12)


def test_weighted_gradient_matches_finite_differences():
    x,starts,targets,w=sample();weights=np.asarray([.2,2.]);_,gradient=objective(w,x,starts,targets,weights)
    for i in range(len(w)):
        delta=np.zeros_like(w);delta[i]=1e-6
        numeric=(objective(w+delta,x,starts,targets,weights)[0]-objective(w-delta,x,starts,targets,weights)[0])/2e-6
        assert abs(numeric-gradient[i])<1e-7


def test_balanced_fit_gives_types_equal_mass_and_mean_weight_one():
    options=[(0,'direct'),(1,'cop'),(1,'aux')];x=np.eye(3,len(FEATURES));frames=[]
    for role,count in (('direct',12),('cop',3),('aux',1)):
        gold=[2,0 if role=='direct' else 1,0,role]
        frames.extend([dict(gold=gold,options=options,x=x) for _ in range(count)])
    model=fit(frames);masses=[model['class_weights'][r]*n for r,n in model['type_counts'].items()]
    assert np.allclose(masses,[16/3]*3) and abs(sum(masses)-16)<1e-12


def test_constant_type_offsets_cannot_change_within_type_head_ranking():
    options=[(3,'direct'),(1,'cop'),(2,'cop'),(1,'aux')];scores=np.asarray([3.,1.,2.,0.]);kept=[1,2];offsets=dict(direct=0.,cop=2.,aux=-2.);changed=scores+np.asarray([offsets[r] for _,r in options])
    assert select(scores[kept],[options[j] for j in kept],0,3)==select(changed[kept],[options[j] for j in kept],0,3)==[0,2,3,'cop']
    assert infer(scores,options,0,3,offsets)==[0,2,3,'cop']


def test_macro_calibration_can_trade_frequent_type_for_rare_type():
    options=[(2,'direct'),(1,'cop'),(1,'aux')];frames=[]
    frames.extend([dict(gold=[0,2,2,'direct'],options=options,scores=np.asarray([3.,0.,-10.])) for _ in range(9)])
    frames.append(dict(gold=[0,2,2,'direct'],options=options,scores=np.asarray([1.,0.,-10.])))
    frames.append(dict(gold=[0,1,2,'cop'],options=options,scores=np.asarray([1.,0.,-10.])))
    frames.append(dict(gold=[0,1,2,'aux'],options=options,scores=np.asarray([-10.,-10.,1.])))
    micro=calibrate(frames,'micro')['selected'];macro=calibrate(frames,'macro')['selected']
    assert micro['offsets']==dict(direct=0.,cop=0.,aux=0.)
    assert macro['macro_recall']>micro['macro_recall'] and macro['correct']==micro['correct']
