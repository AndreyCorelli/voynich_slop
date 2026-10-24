import pytest
from voynich_smt.opaque_class_tags import inject


def test_classes_never_reveal_identity_or_mutate_original():
    p=[dict(sent_id='s',tokens=[dict(id='a',anchor='secret',tag='CCONJ'),dict(id='b',anchor='given',tag='ADP')])]
    q=inject(p,{'a'},{'a':'ADP'})
    assert q[0]['tokens'][0]==dict(id='a',anchor=None,tag='ADP')
    assert q[0]['tokens'][1]==p[0]['tokens'][1]
    assert p[0]['tokens'][0]['anchor']=='secret'
    assert inject(p,{'a'})[0]['tokens'][0]['tag']=='X'


def test_rejects_non_target_and_invalid_classes():
    with pytest.raises(ValueError):inject([],{'a'},{'b':'ADP'})
    with pytest.raises(ValueError):inject([],{'a'},{'a':'NOUN'})
