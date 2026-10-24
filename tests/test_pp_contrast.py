from voynich_smt.pp_contrast import features,train,score


def token(word,pos,case='',number='',gender=''):
    return dict(word=word,pos=pos,case=case,number=number,gender=gender)


def test_government_disambiguates_same_distance_case_alternatives():
    tokens=[token('ad','ADP'),token('urbem','NOUN','Acc')];c=dict(prep=0,head=1,left=0,right=1,case='Acc');model=train([(tokens,c)]*5)
    good=score(model,tokens,c);bad=score(model,tokens,dict(c,case='Abl'))
    assert good['structural']>bad['structural']
    assert good['components']['distance']==bad['components']['distance']
    assert good['components']['boundary']==bad['components']['boundary']


def test_case_intervention_changes_agreement_without_changing_observation():
    tokens=[token('in','ADP'),token('magna','ADJ','Abl','Sing','Fem'),token('urbe','NOUN','Abl','Sing','Fem')];c=dict(prep=0,head=2,left=0,right=2,case='Abl')
    assert features(tokens,c)['agreement']=='match'
    assert features(tokens,dict(c,case='Acc'))['agreement']=='mismatch'
    assert tokens[2]['case']=='Abl'


def test_scores_ignore_reference_heads_and_relations():
    tokens=[token('ad','ADP'),token('urbem','NOUN','Acc')];c=dict(prep=0,head=1,left=0,right=1,case='Acc');model=train([(tokens,c)])
    original=score(model,tokens,c)
    for t in tokens:t.update(head=99,rel='deliberately_wrong')
    assert score(model,tokens,c)==original


def test_unseen_preposition_does_not_invent_government_evidence():
    tokens=[token('ad','ADP'),token('urbem','NOUN','Acc')];c=dict(prep=0,head=1,left=0,right=1,case='Acc');model=train([(tokens,c)])
    tokens[0]['word']='unseen'
    assert score(model,tokens,c)['components']['government']==score(model,tokens,dict(c,case='Abl'))['components']['government']
