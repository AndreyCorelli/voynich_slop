import pytest
from voynich_smt.grammar_lexical_bridge import pos_model,candidate_pos,candidate_tokens,objective_value,permutations,structural_lift,map_cipher


def test_candidate_pos_uses_source_dictionary_and_unknown_not_target_tags():
    model=pos_model([[dict(word='a',pos='ADP'),dict(word='erat',pos='AUX'),dict(word='erat',pos='AUX'),dict(word='homo',pos='NOUN')]])
    assert candidate_pos('erat',model,[dict(pos='V')])==('AUX','source_word')
    assert candidate_pos('ignotum',model,[dict(pos='V')])==('AUX','dictionary_prior')
    assert candidate_pos('unknown',model,[])==('X','unknown')
    tokens,counts=candidate_tokens(['erat','unknown'],model,{})
    assert tokens[0]['features']=={} and tokens[0]['head'] is None and counts['unknown']==1


def test_objective_is_optional_edge_utility_minus_soft_competition():
    frames=[dict(subject=0,predicates=[3],scores=[2.]),dict(subject=1,predicates=[3],scores=[1.])]
    assert objective_value(frames,{0:3,1:3},-1.,2.)==dict(edge_utility=5.,competition_cost=2.,total=3.,attached=2)
    assert objective_value(frames,{0:None,1:None},-1.,2.)['total']==0.


def test_shuffle_has_no_word_or_frequency_side_channel():
    from collections import Counter
    words=['a','b','a','c'];ps=permutations(4)
    assert ps==permutations(4) and all(Counter(words[j] for j in p)==Counter(words) for p in ps)
    assert structural_lift(5.,[5.]*5)==0.


def test_cipher_renaming_does_not_change_scorer_input():
    assert map_cipher(['x','y','x'],{'x':'homo','y':'est'})==map_cipher(['Q','P','Q'],{'Q':'homo','P':'est'})


def test_lexical_projection_does_not_invent_known_pos_for_missing_word():
    model=pos_model([[dict(word='homo',pos='NOUN')]])
    assert candidate_pos('absent',model,[])[0]=='X'
    assert candidate_tokens(['absent'],model,{})[0][0]['pos']=='X'
