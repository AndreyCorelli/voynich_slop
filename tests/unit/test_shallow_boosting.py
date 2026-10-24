from dataclasses import asdict
import json
import numpy as np
import pytest
from voynich_smt.shallow_boosting import ShallowBoostedClassifier


def test_small_nonlinear_model_learns_interaction_and_reduces_logistic_loss():
    x=np.array([[0.,0.],[0.,1.],[1.,0.],[1.,1.]]*40)
    # OR has a useful first split and needs a second split for exact separation.
    y=np.array([0.,1.,1.,1.]*40)
    model=ShallowBoostedClassifier.fit(x,y);z=model.logits(x)
    loss=lambda zz:np.mean(np.logaddexp(0,zz)-y*zz)
    assert loss(z)<loss(np.full(len(y),model.intercept))
    assert np.mean(model.probability(x)[y==0])<np.mean(model.probability(x)[y==1])
    restored=ShallowBoostedClassifier(**json.loads(json.dumps(asdict(model))))
    assert np.array_equal(restored.logits(x),z)
    assert asdict(ShallowBoostedClassifier.fit(x,y))==asdict(model)


def test_capacity_constraints_hold_and_small_samples_cannot_split():
    x=np.arange(30.).reshape(-1,1);y=np.array([0.]*15+[1.]*15)
    model=ShallowBoostedClassifier.fit(x,y)
    assert all('feature' not in t for t in model.trees)
    def check(node,depth=0):
        assert depth<=2 and node['count']>=20
        if 'feature' in node:check(node['left'],depth+1);check(node['right'],depth+1)
        else:assert abs(node['value'])<=1
    large=ShallowBoostedClassifier.fit(np.tile(x,(4,1)),np.tile(y,4))
    for tree in large.trees:check(tree)
    with pytest.raises(ValueError):model.logits([[1.,2.]])


def test_joint_depth_two_search_can_learn_xor_without_univariate_signal():
    x=np.array([[0.,0.],[0.,1.],[1.,0.],[1.,1.]]*40)
    y=np.array([0.,1.,1.,0.]*40)
    model=ShallowBoostedClassifier.fit(x,y)
    assert np.all((model.logits(x)>0)==y.astype(bool))


def test_diagnostic_screen_treats_decimal_gain_threshold_as_inclusive():
    from benchmarks.grammar_nonlinear_contrasts_iteration13 import nonlinear_screen
    def result(accuracy,auc):
        return {'matched_auc':auc,'matched_preference':{'pairs':40,'accuracy':accuracy},
            'same_child_preference':{'pairs':20,'accuracy':accuracy}}
    evaluations={'nonlinear_rich':result(.6,.65),'nonlinear_distance':result(.5,.5)}
    assert nonlinear_screen(evaluations)['passed']  # .6-.5 is +10 points.
    evaluations['nonlinear_rich']['matched_preference']['accuracy']=.599
    assert not nonlinear_screen(evaluations)['passed']
