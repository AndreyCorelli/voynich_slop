from copy import deepcopy
import pytest
from voynich_smt.factor_morphology import target,fit,calibrate,predict


def token(word='urbem',pos='NOUN',case='Acc',number='Sing',person='',form=''):
    return dict(word=word,pos=pos,features=dict(Case=case,Number=number,Person=person,VerbForm=form))


def test_expanded_number_uses_oblique_annotations_matched_does_not():
    t=token()
    assert target(t,'number','expanded')=='Sing'
    assert target(t,'number','matched') is None
    assert target(t,'role','expanded')==target(t,'role','matched')=='NO'


def test_expanded_role_can_use_nominative_with_missing_person():
    t=token('qui','PRON','Nom','Sing','')
    assert target(t,'role','expanded')=='YES'
    assert target(t,'role','matched') is None
    assert target(t,'number','expanded')=='Sing'
    assert target(t,'person','expanded') is None


def test_expanded_person_uses_pronoun_annotations_outside_nominative():
    t=token('me','PRON','Acc','Sing','1')
    assert target(t,'person','expanded')=='1'
    assert target(t,'person','matched') is None


def test_calibration_keeps_training_model_fixed_and_allocates_total_budget():
    rows=[[token()],[token('urbs',case='Nom')]]*10;model=fit(rows,'expanded');saved=deepcopy(model);policies=calibrate(model,rows)
    assert model==saved
    assert policies['total99']['classes']['number/nominal/Sing']['feature_alpha']==pytest.approx(.005)
    assert policies['total99']['classes']['role/pronoun/YES']['feature_alpha']==pytest.approx(.01/3)
    assert policies['set99']['classes']['number/nominal/Sing']['feature_alpha']==.01


def test_composed_probabilities_normalize_and_sets_nest_without_gold_arguments():
    rows=[[token()],[token('urbs',case='Nom')]]*10;model=fit(rows,'expanded');policy=calibrate(model,rows);out=predict(model,policy,'unknown','NOUN')
    assert sum(out['probabilities'])==pytest.approx(1)
    assert out['component_probabilities']['person']==[0.,0.,1.]
    assert set(out['sets']['set95'])<=set(out['sets']['set99'])<=set(out['sets']['total99'])
    with pytest.raises(TypeError):predict(model,policy,'unknown','NOUN',features={'Number':'Sing'})


def test_component_missingness_is_separate_and_nonfinite_number_can_train():
    t=token('amantes','VERB','Nom','Plur','',form='Part')
    assert target(t,'role','expanded')=='NO'
    assert target(t,'number','expanded')=='Plur'
    assert target(t,'person','expanded') is None
    assert target(t,'number','matched') is None
