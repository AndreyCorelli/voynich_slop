import pytest
from benchmarks.clean_latin_prefix import boundary, truncate_witness


def row(size,status):
    return {'word_count':size,'result':{'status':status}}


def test_unknown_does_not_certify_or_move_prefix_boundary():
    result=boundary([row(3,'SAT'),row(23,'UNSAT'),row(13,'UNKNOWN')])
    assert result['largest_verified_sat']==3
    assert result['smallest_proved_unsat']==23
    assert result['unresolved_sizes']==list(range(4,23))
    assert not result['minimality_proven']


def test_adjacent_sat_unsat_certify_shortest_prefix():
    result=boundary([row(3,'SAT'),row(13,'SAT'),row(14,'UNSAT'),row(23,'UNSAT')])
    assert result['minimality_proven']
    assert result['unresolved_sizes']==[]
    assert result['smallest_proved_unsat']==14


def test_contradictory_monotone_prefix_certificates_are_rejected():
    with pytest.raises(RuntimeError):boundary([row(14,'SAT'),row(13,'UNSAT')])


def test_truncation_keeps_choices_for_plaintext_tokens_without_mutating_source():
    source={'plaintext':{'words':[['a','b'],['a'],['b','b']]},
            'choices':[0,1,1,0,1],'segmentation':[[0,1,3],[0,2],[0,1,3]],
            'encoder':{'codebook':{'a':[['x'],['y','z']]}}}
    prefix=truncate_witness(source,2)
    assert prefix['choices']==[0,1,1]
    assert prefix['segmentation']==[[0,1,3],[0,2]]
    prefix['encoder']['codebook']['a'][0].append('q')
    assert len(source['plaintext']['words'])==3
    assert source['choices']==[0,1,1,0,1]
    assert source['encoder']['codebook']['a'][0]==['x']
