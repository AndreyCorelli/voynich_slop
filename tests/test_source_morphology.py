from copy import deepcopy
import pytest
from voynich_smt.source_morphology import fit,label,labels,probabilities,calibrate,predict,domains


def token(word,pos='VERB',form='Fin',number='Sing',person='3',case=''):
    return dict(word=word,pos=pos,features=dict(VerbForm=form,Number=number,Person=person,Case=case))


def policies(model,rows):
    return {name:calibrate(model,rows,alpha) for name,alpha in (('set95',.05),('set99',.01))}


def test_suffix_transfer_to_unseen_form_is_source_only_and_normalized():
    rows=[[token('amant',number='Plur')],[token('laudant',number='Plur')],[token('amat')]]*6;model=fit(rows);p=probabilities(model,'portant','VERB');classes=labels('verbal')
    assert 'portant\tVERB' not in model['words']
    assert p[classes.index('Plur:3')]>p[classes.index('Sing:3')]
    assert sum(p)==pytest.approx(1) and min(p)>0


def test_calibration_does_not_add_heldout_forms_to_dictionary():
    model=fit([[token('amat')]]);original=deepcopy(model);calibrate(model,[[token('portant',number='Plur')]],.01)
    assert model==original and 'portant\tVERB' not in model['words']


def test_sparse_class_threshold_includes_class_without_unearned_certainty():
    model=fit([[token('amat')]]);policy=calibrate(model,[[token('amat')]]*18,.05)
    assert policy['classes']['verbal/Sing:3']['threshold']==0
    assert policy['classes']['verbal/Plur:2']['n']==0 and policy['classes']['verbal/Plur:2']['threshold']==0
    policy=calibrate(model,[[token('amat')]]*19,.05)
    assert policy['classes']['verbal/Sing:3']['rank']==19 and policy['classes']['verbal/Sing:3']['threshold']>0


def test_dictionary_unknown_fallback_preserves_alternatives_and_top1_is_narrow():
    model=fit([[token('amat')]]);out=predict(model,policies(model,[[token('amat')]]),'unknown','VERB')
    assert out['sets']['dictionary']==labels('verbal') and len(out['sets']['top1'])==1
    assert set(out['sets']['set95'])<=set(out['sets']['set99'])


def test_inference_cannot_receive_reference_morphology_and_domains_ignore_it():
    model=fit([[token('amat')]]);p=policies(model,[[token('amat')]]);out=predict(model,p,'amat','VERB')
    with pytest.raises(TypeError):predict(model,p,'amat','VERB',features={'Number':'Plur'})
    a=token('amat');b=token('amat',form='Inf',number='Plur');b.update(head=99,rel='wrong')
    assert domains([a],{'amat\tVERB':out},'set99')==domains([b],{'amat\tVERB':out},'set99')


def test_missing_nominative_person_is_not_mislabeled_as_non_subject():
    assert label(token('qui','PRON',case='Nom',person='')) is None
    assert label(token('urbem','NOUN',case='Acc',number=''))=='OTHER'
    assert label(token('urbes','NOUN',case='Nom',number='Plur',person=''))=='Plur:3'
    assert label(token('amare',form='Inf',number='',person=''))=='OTHER'
