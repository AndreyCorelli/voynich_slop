from itertools import combinations
import pytest
from benchmarks.word_boundary_edits import alignments,emission_lengths,uninterrupted


def brute(words,cipher,emissions,budget):
    stream=''.join(cipher);old=set();p=0
    for w in cipher[:-1]:p+=len(w);old.add(p)
    out=set()
    for count in range(max(1,len(cipher)-budget),min(len(words),len(cipher)+budget)+1):
        for cuts in combinations(range(1,len(stream)),count-1):
            edits=len(set(cuts)^old)
            if edits>budget:continue
            edges=(0,)+cuts+(len(stream),)
            if all(edges[i+1]-edges[i] in emissions[words[i]] for i in range(count)):
                out.add((count,cuts,edits))
    return out


@pytest.mark.parametrize('cipher',[['ab','cd','ef'],['a','bc','def'],['abc','def']])
@pytest.mark.parametrize('words',[['a']*5,['aa','b','cc','d','e']])
@pytest.mark.parametrize('budget',[0,1,2])
def test_dp_matches_exhaustive_boundary_search(cipher,words,budget):
    emissions={w:emission_lengths(w,[]) for w in words}
    actual={(a['word_count'],tuple(a['cuts']),a['edits']) for a in alignments(words,cipher,emissions,budget)}
    assert actual==brute(words,cipher,emissions,budget)


def test_moving_boundary_costs_two_and_preserves_characters():
    words=['aa','b'];cipher=['a','bcd'];emissions={'aa':(2,), 'b':(2,)}
    assert not list(alignments(words,cipher,emissions,1))
    result=list(alignments(words,cipher,emissions,2))
    assert len(result)==1
    assert result[0]['edits']==2 and result[0]['removed_cuts']==[1] and result[0]['added_cuts']==[2]
    assert ''.join(result[0]['ciphertext_words'])=='abcd'


def test_join_and_split_change_attested_word_count():
    assert list(alignments(['ab'],['a','b'],{'ab':(2,)},1))[0]['removed_cuts']==[1]
    assert list(alignments(['a','b'],['ab'],{'a':(1,),'b':(1,)},1))[0]['added_cuts']==[1]


def test_repetition_applies_only_to_complete_reconstructed_words():
    a=list(alignments(['a','b'],['x','x'],{'a':(1,),'b':(1,)},0))[0]
    assert not a['repetition_compatible']
    a=list(alignments(['ab'],['x','x'],{'ab':(2,)},1))[0]
    assert a['repetition_compatible']


def test_source_gaps_and_parts_remain_separate():
    assert list(uninterrupted([['a',None,'b'],['c','d']]))==[(0,['a']),(2,['b']),(3,['c','d'])]


def test_optional_contractions_consider_all_emission_lengths():
    rules=[{'id':'est','expansion':'est','position':'whole'}]
    assert emission_lengths('est',rules)==tuple(range(1,10))
