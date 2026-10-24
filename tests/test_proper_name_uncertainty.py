import pytest
from voynich_smt.proper_name_uncertainty import candidates


def model(n):
    return {'words':{'number/name\tPROPN':{'Sing':n}}}


@pytest.mark.parametrize('n,policy,widen',[(0,'proper_unseen',True),(1,'proper_unseen',False),(4,'proper_sparse5',True),(5,'proper_sparse5',False),(20,'proper_all',True)])
def test_fit_support_gate(n,policy,widen):
    original=['OTHER','Plur:3']
    result=candidates('name','PROPN',original,model(n),policy)
    assert ('Sing:3' in result)==widen
    assert set(original)<=set(result)


def test_eligibility_and_other_pos_preserved():
    assert candidates('name','PROPN',['OTHER'],model(0),'proper_all')==['OTHER']
    assert candidates('name','PROPN',[],model(0),'proper_all')==[]
    assert candidates('name','NOUN',['Plur:3'],model(0),'proper_all')==['Plur:3']


def test_inputs_unchanged_and_invalid_policy_rejected():
    original=['Plur:3'];fitted=model(0)
    candidates('name','PROPN',original,fitted,'proper_all')
    assert original==['Plur:3'] and fitted==model(0)
    with pytest.raises(ValueError):candidates('name','PROPN',original,fitted,'bad')
