import math
from itertools import product
import pytest
from voynich_smt.word_mapping.ngram import BOS, EOS, NgramModel
from voynich_smt.word_mapping.uniform_backoff import UniformBackoffModel
from voynich_smt.widening_mapping import expanded_model
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.incremental import IncrementalScorer
from voynich_smt.word_mapping.objective import objective_score


def test_uniform_backoff_normalized_with_boundaries_and_unseen_forms():
    original = expanded_model(NgramModel.train([('a','b'),('a','a')]), ['unseen'])
    model = UniformBackoffModel.from_model(original)
    assert model.identity != original.identity
    contexts = [BOS, *model.form_ids.values()]
    for a,b in product(contexts,repeat=2):
        assert math.isclose(sum(model.probability(a,b,c) for c in range(EOS,len(model.vocabulary)+3)),1,abs_tol=1e-12)
    unseen = model.form_ids['unseen']
    # No observed transitions from the unseen context: training membership alone is neutral.
    assert model.probability(unseen,unseen,model.form_ids['a']) == model.probability(unseen,unseen,unseen)
    # Actual observed contextual evidence still matters.
    assert model.probability(BOS,model.form_ids['a'],model.form_ids['b']) > model.probability(BOS,model.form_ids['a'],unseen)
    with pytest.raises(ValueError): model.probability(BOS,BOS,BOS)


def test_incremental_changes_equal_full_rescoring():
    model = UniformBackoffModel.from_model(expanded_model(NgramModel.train([('a','b','a')]),['unseen']))
    forms = ('a','b','unseen')
    segments = (('x','y','x'),('y','x'))
    mapping = WordMapping(forms,{'x':0,'y':1})
    scorer = IncrementalScorer(model,segments,mapping,injective=True)
    for changes in [{'x':2},{'x':1,'y':0}]:
        proposal=scorer.propose(changes)
        altered=WordMapping(forms,{**mapping.assignments,**changes})
        expected=objective_score(model,segments,altered,injective=True)-objective_score(model,segments,mapping,injective=True)
        assert math.isclose(scorer.delta(proposal),expected,abs_tol=1e-12)
