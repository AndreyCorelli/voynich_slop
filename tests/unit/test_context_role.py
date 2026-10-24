import numpy as np
from benchmarks.latin_context_role import context, role, Model


def test_masked_target_does_not_enter_features():
    assert context(('in','terra','sumus'),1)==context(('in','terram','sumus'),1)
    assert context(('in','terra','sumus'),1)!=context(('ad','terra','sumus'),1)


def test_roles_keep_only_oracle_relevant_features():
    t={'pos':'NOUN','features':{'Case':'Nom','Number':'Sing','Gender':'Fem','Person':'3'}}
    assert role(t)==('N','NOM','S','F','_')


def test_dictionary_compatibility_accepts_alternative_lexemes():
    model=Model.__new__(Model);model.labels=[('N','NOM','S','F','_'),('N','ACC','S','F','_')]
    def entry(case):return [{'inflections':[{'part_of_speech':'N','features':{'Case':case,'Number':'S','Gender':'F'}}]}]
    e={'terra':entry('NOM'),'rosa':entry('NOM'),'terram':entry('ACC')}
    assert np.array_equal(model.compatible(e,'terra'),model.compatible(e,'rosa'))
    assert not np.array_equal(model.compatible(e,'terra'),model.compatible(e,'terram'))
