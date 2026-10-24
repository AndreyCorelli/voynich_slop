from benchmarks.known_passage_keys import solve_case
from voynich_smt.models.text import Text
from voynich_smt.models.alphabet import Alphabet


def test_same_length_word_positions_are_fixed_not_union_dictionary():
    # With H1 impossible; even H2 cannot encode one a as three distinct glyphs.
    words=('a','a','a','b')
    result=solve_case(words,Text.from_string('x y z w'),[],1000)
    assert result['result']['status']=='UNSAT'


def test_contraction_gate_sat_and_letter_only_unsat():
    rules=[{'id':'ae','expansion':'ae','position':'any'}]
    assert solve_case(('ae',),Text.from_string('x'),[],1000)['result']['status']=='UNSAT'
    result=solve_case(('ae',),Text.from_string('x'),rules,1000,Alphabet(tuple('xyz')))
    assert result['result']['status']=='SAT'
    assert result['expanded_plaintext']==['ae']


def test_equal_length_contraction_paths_all_retained():
    rules=[{'id':'ae','expansion':'ae','position':'any'},
           {'id':'ea','expansion':'ea','position':'any'}]
    result=solve_case(('aea',),Text.from_string('xy'),rules,1000,Alphabet(tuple('xyzuvw')))
    assert result['result']['status']=='SAT'
    assert ('<ae>','a') in result['position_unitizations'][0]
    assert ('a','<ea>') in result['position_unitizations'][0]
    assert result['expanded_plaintext']==['aea']
