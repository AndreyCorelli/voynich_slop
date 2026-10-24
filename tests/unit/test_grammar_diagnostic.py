from dataclasses import asdict
from itertools import product
import math
import pytest
from voynich_smt.grammar_diagnostic import MorphAnalysis,LatinAdapter,BoundaryModel,GrammarScorer


def reading(pos,**features):
    return MorphAnalysis(pos,tuple(sorted(features.items())))


class Adapter(LatinAdapter):
    def __init__(self, lexicon):self.lexicon=lexicon
    def analyze(self, word):return tuple(self.lexicon.get(word,()))


def scorer():
    nominal=reading('N',Case='NOM',Gender='F',Number='S')
    lexicon={'puella':[nominal], 'bona':[reading('ADJ',Case='NOM',Gender='F',Number='S')],
        'bonus':[reading('ADJ',Case='NOM',Gender='M',Number='S')],
        'amat':[reading('V',Mood='IND',Person='3',Number='S')],
        'amant':[reading('V',Mood='IND',Person='3',Number='P')],
        'ad':[reading('PREP')], 'urbem':[reading('N',Case='ACC',Number='S',Gender='F')],
        'urbe':[reading('N',Case='ABL',Number='S',Gender='F')],
        'bene':[reading('ADV')]}
    return GrammarScorer(Adapter(lexicon),BoundaryModel(12))


def test_agreement_both_orders_and_subject_omission():
    s=scorer()
    for good,bad in [(('bona','puella','amat'),('bonus','puella','amat')),
                     (('puella','amat'),('puella','amant')),
                     (('ad','urbem','amat'),('ad','urbe','amat'))]:
        assert s.score(good,latent=False).total>s.score(bad,latent=False).total
    assert s.score(('amat',),latent=False).components['subject']==0
    assert s.score(('puella','bona','amat'),latent=False).components['modifier']==0


def test_unknown_and_extra_analyses_do_not_directly_add_rewards():
    s=scorer()
    unknown=s.score(('zzzz',),latent=False)
    assert unknown.known_tokens==0
    assert sum(unknown.components.values())==unknown.total
    a=s.adapter
    before=s.score(('bona','puella','amat'),latent=False)
    a.lexicon['bona']*=4
    assert s.score(('bona','puella','amat'),latent=False)==before


def test_latent_dp_matches_exhaustive_two_segment_partitions():
    s=scorer();s.boundary=BoundaryModel(6,max_length=8)
    tokens=('bona','puella','amat','bene')*3
    score=s.score(tokens)
    # Length 12 and max 8 imply two or three legal segments.
    options=[]
    for n in [2,3]:
        for lengths in product(range(4,9),repeat=n):
            if sum(lengths)!=len(tokens):continue
            offset=0;value=0
            for length in lengths:
                value+=s.score(tokens[offset:offset+length],latent=False).total+s.boundary.log_prior[length]
                offset+=length
            options.append(value)
    assert math.isclose(score.total,max(options),abs_tol=1e-12)
    assert score.boundaries[-1]==len(tokens)
    assert all(b-a>=4 for a,b in zip((0,)+score.boundaries,score.boundaries))


def test_no_reference_boundary_argument_and_empty_input():
    s=scorer()
    assert s.score(()).total==0
    with pytest.raises(TypeError):s.score(('amat',),reference_boundaries=[1])
