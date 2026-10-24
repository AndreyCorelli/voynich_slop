from voynich_smt.context_evidence_loss import remove_suffix_type


def test_preserves_prefix_and_sentence_slots_even_when_empty():
    public = [dict(sent_id=str(i), tokens=[dict(id='a'), dict(id='b')]) for i in range(3)]
    result = remove_suffix_type(public, 'a', 1)
    assert result[0] == public[0]
    assert [s['sent_id'] for s in result] == ['0', '1', '2']
    assert all(s['tokens'] == [dict(id='b')] for s in result[1:])
    empty = remove_suffix_type(result, 'b', 1)
    assert all(s['tokens'] == [] for s in empty[1:])
    result[0]['tokens'][0]['id'] = 'changed'
    assert public[0]['tokens'][0]['id'] == 'a'
