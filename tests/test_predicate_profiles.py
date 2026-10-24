from copy import deepcopy
import numpy as np
from voynich_smt.predicate_profiles import build_profiles,vectorize,train,probability,transfer
from voynich_smt.predicate_case import probability as lexical_probability


def t(word,pos,head,rel,case='',lemma=None):
    return dict(word=word,pos=pos,head=head,rel=rel,case=case,lemma=lemma or word)


def test_profiles_ignore_case_and_lexical_identity_of_in_complement():
    tokens=[t('mittit','VERB',None,'root',lemma='mitto'),t('in','ADP',2,'case'),t('urbem','NOUN',0,'obl','Acc'),t('milites','NOUN',0,'obj','Acc')]
    original=build_profiles([tokens]);altered=deepcopy(tokens);altered[2].update(case='Abl',lemma='entirely_different')
    assert build_profiles([altered])==original
    assert original['excluded_subtrees']==1
    assert 'argument:obj:milites' in original['profiles']['mitto']
    assert all('urbem' not in f for f in original['profiles']['mitto'])


def test_indirect_in_subtree_is_also_excluded():
    tokens=[t('est','VERB',None,'root',lemma='sum'),t('pars','NOUN',0,'nsubj','Nom'),t('urbe','NOUN',1,'nmod','Abl'),t('in','ADP',2,'case')]
    assert build_profiles([tokens])['profiles']=={}


def test_transfer_excludes_self_and_borrows_from_another_predicate():
    profiles={'held':{'frame:obj:NOUN':2},'donor':{'frame:obj:NOUN':1},'other':{'frame:obl:NOUN':1}}
    records=[dict(predicate='held',case='Abl')]*10+[dict(predicate='donor',case='Acc')]*10
    model=train(records,profiles);p,neighbors=transfer(model,'held')
    assert [r['predicate'] for r in neighbors]==['donor']
    assert p>.5
    assert probability(model,'held',True)<p


def test_unseen_in_profile_can_transfer_but_missing_profile_is_exact_backoff():
    model=train([dict(predicate='donor',case='Acc')]*3+[dict(predicate='negative',case='Abl')]*3,{'new':{'shared':1},'donor':{'shared':2},'negative':{'different':1}})
    assert 'new' not in model['counts']
    assert probability(model,'new')>model['base']
    assert probability(model,'no_profile')==model['base']
    assert probability(model,None)==model['base']
    assert probability(model,'donor')==lexical_probability(model,'donor') # no other similar donor


def test_vectors_are_source_tfidf_normalized_and_order_independent():
    a=vectorize({'a':{'x':1,'y':2},'b':{'x':3}});b=vectorize({'b':{'x':3},'a':{'y':2,'x':1}})
    assert all(np.allclose(a[k],b[k]) and np.isclose(np.linalg.norm(a[k]),1) for k in a)
