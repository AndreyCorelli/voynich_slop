import math
import numpy as np
import pytest
from voynich_smt.structural_language import StructuralLanguageModel
from voynich_smt.structural_search import ProfileScorer,ProfileSearch


def entry(pos, **features):
    return [{'enclitic':None,'inflections':[{'part_of_speech':pos,'features':features}]}]


def test_compiled_forward_and_transactional_changes_match_python():
    entries={'a':entry('N',Case='NOM'),'b':entry('V',Number='S'),
             'amb':entry('N',Case='NOM')+entry('N',Case='ACC'),'in':entry('PREP')}
    model=StructuralLanguageModel(entries).fit((('in','a','b'),)*10)
    forms=('a','b','amb','in','unknown')
    profiles=tuple(model.emissions(w) for w in forms)
    segments=(('x','y','x'),('z','x'),('y',))
    assignments={'x':2,'y':1,'z':3}
    scorer=ProfileScorer(model,profiles,segments,assignments)
    def full():return model.score(tuple(tuple(forms[scorer.assignments[scorer.ids[w]]] for w in s) for s in segments))
    assert scorer.score==pytest.approx(full())
    for changes in ({0:0},{1:4},{0:2,2:1},{}):
        old=scorer.assignments.copy();before=scorer.score
        proposal=scorer.propose(changes)
        assert np.array_equal(scorer.assignments,old)
        scorer.commit(changes,proposal)
        assert scorer.score==pytest.approx(full())
        assert scorer.score-before==pytest.approx(proposal[0])
        scorer.validate()
    with pytest.raises(ValueError):scorer.propose({0:999})


def test_anchors_capacities_and_deterministic_search():
    entries={'a':entry('N',Case='NOM'),'b':entry('V',Number='S'),'in':entry('PREP')}
    model=StructuralLanguageModel(entries).fit((('in','a','b'),)*10)
    profiles=tuple(model.emissions(w) for w in ('a','b','in'))
    results=[]
    for _ in range(2):
        scorer=ProfileScorer(model,profiles,(('x','y','z'),),{'x':2,'y':1,'z':0})
        search=ProfileSearch(scorer,[1,1,1],[10,10,10],{0:2},seed=3,steps=400)
        search.advance(100);search.advance(300)
        assert list(scorer.assignments).count(2)==1 and scorer.assignments[0]==2
        assert math.isclose(search.best_score,model.score((tuple(('a','b','in')[i] for i in search.best),)),abs_tol=1e-8)
        results.append((list(search.best),dict(search.statistics),search.trace))
    assert results[0]==results[1]
