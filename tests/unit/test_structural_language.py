import itertools
import math
import pytest
from voynich_smt.structural_language import StructuralLanguageModel, BOS, EOS


def entry(pos, **features):
    return [{'enclitic': None, 'inflections': [{'part_of_speech':pos, 'features':features}]}]


def fixture():
    entries={'a':entry('N', Case='NOM', Number='S'), 'b':entry('V', Number='S', Person='3'),
             'replacement':entry('N', Case='NOM', Number='S'), 'object':entry('N',Case='ACC',Number='S'),
             'ambiguous':entry('N',Case='NOM',Number='S')+entry('N',Case='ACC',Number='S'),
             'in':entry('PREP'),'ad':entry('PREP')}
    return StructuralLanguageModel(entries).fit((('a','b'),)*100)


def test_forward_matches_exhaustive_latent_paths():
    model=fixture()
    words=('ambiguous','b','ambiguous')
    possibilities=[model.emissions(w) for w in words]
    probability=0
    for path in itertools.product(*possibilities):
        states=(BOS,*path,EOS)
        p=math.exp(sum(model.log_transition(a,b) for a,b in zip(states,states[1:])))
        probability+=p/math.prod(map(len,possibilities))
    assert model.score((words,)) == pytest.approx(math.log(probability))


def test_lexical_tolerance_and_broken_order():
    model=fixture()
    assert model.score((('a','b'),)) == model.score((('replacement','b'),))
    assert model.score((('a','b'),)) > model.score((('b','object'),))
    assert model.emissions('in') != model.emissions('ad')
    assert model.score((('unrecognized','b'),)) == model.score((('other_unrecognized','b'),))
    assert model.score((('a',),('b',))) != model.score((('a','b'),))


def test_lifecycle_and_smoothing():
    with pytest.raises(ValueError):
        StructuralLanguageModel({},alpha=0)
    model=StructuralLanguageModel({})
    with pytest.raises(ValueError):
        model.score((('a',),))
    with pytest.raises(ValueError):
        model.fit(())
    model=fixture()
    with pytest.raises(ValueError):
        model.fit((('a',),))
    assert sum(math.exp(model.log_transition(BOS,s)) for s in (*model.states,('OUTSIDE',))) == pytest.approx(1)
