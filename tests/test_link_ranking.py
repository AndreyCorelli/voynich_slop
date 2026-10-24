from voynich_smt.link_ranking import features,best,select,anchored_utility


def test_gold_and_words_do_not_affect_features():
    tokens=[dict(pos=p,features={'Number':'Sing'},head=0,rel='nsubj',word='latin') for p in ('NOUN','SCONJ','VERB','CCONJ','AUX')]
    masked=[dict(t,features={},head=None,rel='?',word='?') for t in tokens]
    assert features(tokens,0,4)==features(masked,0,4)==dict(distance=4,verbal=1,subordinator=1,coordinator=1)
    assert features(tokens,4,0)==features(tokens,0,4)


def test_explicit_ties_and_no_candidates():
    obs={(0,2):dict(distance=2,verbal=0),(4,2):dict(distance=2,verbal=1)}
    assert best(list(obs),obs)==[(0,2),(4,2)]
    assert best(list(obs),obs,'verbal',1)==[(0,2)]
    assert best([],obs)==[]


def test_other_annotated_link_is_positive_in_selection():
    row=dict(reference=[0,2],pairs=[(0,2),(0,1)],valid={(0,2),(0,1)},observations={(0,2):dict(distance=2),(0,1):dict(distance=1)})
    assert anchored_utility([row],None,0)==1


def test_conservative_selection_when_cues_add_nothing():
    row=dict(reference=[0,1],pairs=[(0,1)],valid={(0,1)},observations={(0,1):dict(distance=1,verbal=0,subordinator=0,coordinator=0)})
    model=select([row],[row])
    assert model['cue'] is None and model['weight']==0
    assert select([],[])['weight']==0
