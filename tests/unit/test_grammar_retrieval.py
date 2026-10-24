import math
import pytest
from voynich_smt.grammar_retrieval import admits,project

def profile(pos,**features):return frozenset({(pos,None,tuple(sorted(features.items())))})

def test_grammar_projection_preserves_joint_analyses():
    reference=profile('N',Case='ACC',Number='S')|profile('N',Case='NOM',Number='P')
    assert not admits(profile('N',Case='ACC',Number='P'),reference,{'Case','Number'})
    assert admits(profile('N',Case='ACC',Number='P'),reference,set())
    assert not admits(profile('V',Case='ACC',Number='S'),reference,set())

def test_unknown_reference_does_not_claim_grammar_failure():
    assert admits(profile('N'),frozenset(),None)
    assert not admits(frozenset(),profile('N'),None)

def test_full_analysis_retains_enclitic_and_features():
    p=profile('N',Case='ACC',Number='S',Gender='F')
    assert project(p,None)==p
    assert project(p,{'Case','Number'})==frozenset({('N',(('Case','ACC'),('Number','S')))})

def test_hidden_spelling_is_absent_from_context_features():
    pytest.importorskip('torch')
    from benchmarks.word_mapping_grammar_inference import context_ids
    a=context_ids(('secret','f','other','secret'),'secret',0,{'f':'in'},['in'])
    b=context_ids(('renamed','f','different','renamed'),'renamed',0,{'f':'in'},['in'])
    assert a==b
    assert a!=context_ids(('renamed','f','different','fourth'),'renamed',0,{'f':'in'},['in'])
    with pytest.raises(ValueError):context_ids(('x',),'x',0,{'x':'answer'},['in'])

def test_ambiguous_label_loss_allows_any_valid_analysis():
    torch=pytest.importorskip('torch')
    from benchmarks.word_mapping_grammar_inference import ambiguity_loss
    values=ambiguity_loss(torch.log(torch.tensor([[.2,.3,.5]])),torch.tensor([[True,True,False]]))
    assert float(values[0])==pytest.approx(-math.log(.5))
