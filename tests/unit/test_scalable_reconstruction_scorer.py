import numpy as np
import pytest
from voynich_smt.word_mapping.scalable.reconstruction_scorer import features, fit_preferences, score
from benchmarks.scalable_latin_reconstruction_scorer import corrupt


def test_context_observes_order_when_unigrams_do_not():
    a='in principio erat uerbum et uerbum erat apud deum'.split()
    b=list(reversed(a))
    assert (features(a,context=False)-features(b,context=False)).nnz==0
    assert (features(a)-features(b)).nnz>0


def test_preference_fit_and_serializable_score(tmp_path):
    a='in principio erat uerbum et uerbum erat apud deum'.split()
    b=list(reversed(a));weights,fit=fit_preferences([features(a)-features(b)])
    path=tmp_path/'weights.npy';np.save(path,weights);loaded=np.load(path)
    assert fit['pairs']==1
    assert score(a,loaded)>score(b,loaded)
    with pytest.raises(ValueError):score([],loaded)


def test_corruption_is_consistent_injective_and_deterministic():
    words='a b a c d b e f g h'.split();result=corrupt(words,1.,7)
    assert result==corrupt(words,1.,7)
    mapping=dict(zip(words,result))
    assert len(set(mapping.values()))==len(mapping)
    assert all(mapping[a]==b for a,b in zip(words,result))
