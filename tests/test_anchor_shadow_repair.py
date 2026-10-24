import pytest
from voynich_smt.anchor_shadow_repair import swap_assignments


def public():
    return [dict(sent_id='s',tokens=[dict(id='a',anchor='in',tag='ADP'),dict(id='b',anchor='et',tag='CCONJ'),dict(id='a',anchor='in',tag='ADP'),dict(id='x',anchor=None,tag='X')])]


def test_blind_swap_preserves_ids_and_changes_every_occurrence():
    source=public();changed=swap_assignments(source,['a','b']);ts=changed[0]['tokens']
    assert [t['id'] for t in ts]==['a','b','a','x']
    assert [t['anchor'] for t in ts]==['et','in','et',None]
    assert [t['tag'] for t in ts]==['CCONJ','ADP','CCONJ','X']
    assert swap_assignments(changed,['a','b'])==source
    assert source[0]['tokens'][0]['anchor']=='in'
    assert swap_assignments(source,None)==source


def test_invalid_or_inconsistent_public_recommendation_rejected():
    with pytest.raises(ValueError):swap_assignments(public(),['a','missing'])
    with pytest.raises(ValueError):swap_assignments(public(),['a','a'])
    inconsistent=public();inconsistent[0]['tokens'][2]['tag']='CCONJ'
    with pytest.raises(ValueError):swap_assignments(inconsistent,['a','b'])
