import pytest
from voynich_smt.context_anchor_repair import repair_prefix


def test_global_pair_can_repair_query_with_only_one_endpoint():
    q=[dict(sent_id='q',tokens=[dict(id='a',anchor='et',tag='CCONJ')])]
    context=q+[dict(sent_id='extra',tokens=[dict(id='b',anchor='in',tag='ADP')])]
    fixed=repair_prefix(q,context,['a','b'])
    assert fixed[0]['tokens']==[dict(id='a',anchor='in',tag='ADP')]
    assert len(fixed)==1 and q[0]['tokens'][0]['anchor']=='et'


def test_zero_affected_query_is_preserved_and_prefix_mismatch_rejected():
    q=[dict(sent_id='q',tokens=[dict(id='x',anchor=None,tag='X')])]
    context=q+[dict(sent_id='extra',tokens=[dict(id='a',anchor='et',tag='CCONJ'),dict(id='b',anchor='in',tag='ADP')])]
    assert repair_prefix(q,context,['a','b'])==q
    with pytest.raises(ValueError):repair_prefix([],[],['a','b'])
    with pytest.raises(ValueError):repair_prefix(q,[],None)
