from copy import deepcopy
import numpy as np
from voynich_smt.typed_predicate_units import gold_unit,choices,matrix,fit,infer,select,FEATURES,BASE_FEATURES


def example(copula=False):
    if copula:
        return [dict(pos='NOUN',head=1,rel='nsubj',features={}),dict(pos='ADJ',head=None,rel='root',features={}),dict(pos='AUX',head=1,rel='cop',features={'VerbForm':'Fin'})]
    return [dict(pos='NOUN',head=2,rel='nsubj',features={}),dict(pos='ADV',head=2,rel='advmod',features={}),dict(pos='VERB',head=None,rel='root',features={'VerbForm':'Fin'})]


def test_gold_units_have_explicit_head_and_role():
    assert gold_unit(example(),0)==[0,2,2,'direct']
    assert gold_unit(example(True),0)==[0,1,2,'cop']
    assert gold_unit(example(),1) is None


def test_candidate_domain_and_vectors_ignore_gold_and_words():
    tokens=example(True);masked=[dict(t,head=None,rel='?',features={},word='?',lemma='?') for t in tokens]
    options=choices(tokens,0,2)
    assert options==[(2,'direct'),(1,'cop'),(1,'aux')]
    assert options==choices(masked,0,2)
    assert np.array_equal(matrix(tokens,0,2,options),matrix(masked,0,2,options))


def test_distance_baseline_selects_type_from_fit_priors_without_true_type():
    tokens=example(True);model=dict(type_counts={'AUX':{'aux':100}},head_pos_counts={'aux':{'ADJ':100}})
    # The annotated type is cop, but the deliberately wrong fit prior predicts aux.
    assert infer(tokens,0,2,model,1)==[0,1,2,'aux']


def test_score_ties_abstain_instead_of_using_candidate_order():
    options=choices(example(True),0,2)
    assert select(np.zeros(len(options)),options,0,2) is None
    assert select(np.array([0.,2.,1.]),options,0,2)==[0,1,2,'cop']


def test_conditional_training_recovers_distinct_units_and_target_indexing():
    frames=[]
    for cop in (False,True):
        tokens=example(cop);gold=gold_unit(tokens,0);options=choices(tokens,0,2)
        frames.extend([dict(sid=str(cop),gold=gold,options=options,x=matrix(tokens,0,2,options),carrier_pos=tokens[2]['pos'],head_pos=tokens[gold[1]]['pos']) for _ in range(10)])
    model=fit(frames)
    assert len(model['weights'])==len(FEATURES)==3*len(BASE_FEATURES)
    assert infer(example(),0,2,model)==[0,2,2,'direct']
    assert infer(example(True),0,2,model)==[0,1,2,'cop']
    original=deepcopy(model)
    infer(example(True),0,2,model)
    assert model==original
