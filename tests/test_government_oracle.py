from copy import deepcopy
from voynich_smt.government_oracle import bundles

def tokens():return [dict(word='in',pos='ADP',head=1,rel='case',features={}),dict(word='urbe',pos='NOUN',head=2,rel='obl',features={'Case':'Abl'}),dict(word='est',pos='VERB',head=None,rel='root',features={'VerbForm':'Fin'})]

def test_true_membership_not_just_nearby_preposition():
    ts=tokens();pp,_=bundles(ts,['ADP','NOUN','VERB'],2)
    assert pp==['oraclePP:present=False']
    assert 'oraclePP:present=True' in bundles(ts,['ADP','NOUN','VERB'],1)[0]

def test_case_values_and_subject_object_labels_not_features():
    ts=tokens();a=bundles(ts,['ADP','NOUN','VERB'],1);ts[1]['features']['Case']='Nom';ts[1]['rel']='nsubj';b=bundles(ts,['ADP','NOUN','VERB'],1);ts[1]['rel']='obj';c=bundles(ts,['ADP','NOUN','VERB'],1)
    assert a==b==c

def test_adjective_inherits_only_declared_phrase_links():
    ts=tokens()+[dict(word='magna',pos='ADJ',head=1,rel='amod',features={})];pos=['ADP','NOUN','VERB','ADJ']
    assert 'oraclePP:inherited=True' in bundles(ts,pos,3)[0]
    ts[3]['rel']='nmod'
    assert bundles(ts,pos,3)[0]==['oraclePP:present=False']

def test_cycles_terminate():
    ts=[dict(word='a',pos='NOUN',head=1,rel='conj'),dict(word='b',pos='NOUN',head=0,rel='conj')]
    assert bundles(ts,['NOUN','NOUN'],0)[0]==['oraclePP:present=False']
