import pytest
from voynich_smt.predicate_case import fit,probability,governor,nearest


def test_unseen_and_missing_predicates_back_off_exactly():
    model=fit([dict(predicate='eo',case='Acc'),dict(predicate=None,case='Abl'),dict(predicate='sum',case='Abl')])
    assert probability(model,'unseen')==model['base']
    assert probability(model,None)==model['base']
    assert probability(model,'eo')>model['base']>probability(model,'sum')


def test_shrinkage_does_not_make_single_observation_certain():
    model=fit([dict(predicate='eo',case='Acc'),dict(predicate='sum',case='Abl')],4)
    assert probability(model,'eo')==pytest.approx(.6)
    assert probability(model,'sum')==pytest.approx(.4)
    stronger=fit([dict(predicate='eo',case='Acc'),dict(predicate='sum',case='Abl')],16)
    assert .5<probability(stronger,'eo')<probability(model,'eo')


def test_oracle_ancestor_and_nearest_can_disagree_and_cycle_terminates():
    tokens=[dict(pos='VERB',head=None),dict(pos='NOUN',head=0),dict(pos='ADP',head=1),dict(pos='VERB',head=0)]
    assert governor(tokens,1)==(0,1)
    assert nearest(tokens,2)==3
    tokens[0]=dict(pos='NOUN',head=1)
    assert governor(tokens,1)==(None,None)


def test_oracle_ancestor_distinguishes_indirect_link():
    tokens=[dict(pos='VERB',head=None),dict(pos='NOUN',head=0),dict(pos='NOUN',head=1)]
    assert governor(tokens,2)==(0,2)


def test_probability_does_not_receive_reference_case_or_head_features():
    model=fit([dict(predicate='eo',case='Acc',head_case='deliberate noise')])
    assert 0<probability(model,'eo')<1
    with pytest.raises(TypeError):probability(model,'eo',case='Abl')
    with pytest.raises(ValueError):fit([dict(predicate='eo',case='Gen')])
