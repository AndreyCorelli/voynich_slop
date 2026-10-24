import numpy as np
import pytest
from voynich_smt.relative_search import PassageScorer


def test_global_replacement_rescores_every_occurrence_and_commit_matches_full():
    calls=[]
    def features(words):
        calls.append(words)
        return np.array([sum({'a':1,'b':2,'d':4}[w] for w in words)/len(words)])
    scorer=PassageScorer([['x','y'],['x']],{'x':'a','y':'b'},features,[1.])
    original=scorer.score
    proposal=scorer.propose({'x':'d'})
    assert set(proposal.sentence_features)=={0,1}
    assert scorer.score==original and scorer.mapping['x']=='a'
    scorer.commit(proposal)
    assert np.isclose(scorer.score,scorer.full_score())
    assert np.isclose(scorer.score,(4+2+4)/3)


def test_injective_swap_allowed_but_collision_rejected():
    scorer=PassageScorer([['x','y']],{'x':'a','y':'b'},lambda words:np.array([1. if words[0]=='a' else 0.]),[1.])
    with pytest.raises(ValueError,match='collision'):scorer.propose({'x':'b'})
    scorer.commit(scorer.propose({'x':'b','y':'a'}))
    assert scorer.mapping=={'x':'b','y':'a'}
    assert scorer.score==scorer.full_score()


def test_unaffected_sentence_is_not_rescored():
    scorer=PassageScorer([['x'],['y']],{'x':'a','y':'b'},lambda words:np.array([len(words)]),[1.])
    proposal=scorer.propose({'x':'d'})
    assert set(proposal.sentence_features)=={0}
