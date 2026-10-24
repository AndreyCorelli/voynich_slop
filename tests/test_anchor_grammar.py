import numpy as np
from voynich_smt import anchor_grammar as ag
from voynich_smt.coarse_government import fold
from benchmarks.grammar_anchor_only_iteration84_pool_control import fold_pool

def sentence(words):return [dict(sent_id='s',tokens=[dict(word=w,pos='NOUN',features={},head=None,rel='root') for w in words])]

def test_rekeying_opaque_ids_preserves_features_and_equality():
    ss=sentence(['in','abc','abc']);a=ag.public_sentences(ss,{'in':'ADP'},'a');b=ag.public_sentences(ss,{'in':'ADP'},'b')
    assert a[0]['tokens'][1]['id']!=b[0]['tokens'][1]['id']
    assert a[0]['tokens'][1]['id']==a[0]['tokens'][2]['id']
    assert [r['features'] for r in ag.public_features(a)]==[r['features'] for r in ag.public_features(b)]

def test_hidden_form_spelling_length_and_goldpos_not_features():
    a=ag.public_features(ag.public_sentences(sentence(['in','abc','abc']),{'in':'ADP'},'a'))
    ss=sentence(['in','MUCHLONGERSECRET','MUCHLONGERSECRET'])
    for t in ss[0]['tokens']:t['pos']='VERB'
    b=ag.public_features(ag.public_sentences(ss,{'in':'ADP'},'a'))
    assert [r['features'] for r in a]==[r['features'] for r in b]
    assert not any('SECRET' in f for r in b for f in r['features'])

def test_unrecognized_function_words_stay_opaque():
    ss=sentence(['cum']);ss[0]['tokens'][0]['pos']='ADP'
    t=ag.public_sentences(ss,{},'a')[0]['tokens'][0]
    assert t['anchor'] is None and t['tag']=='X'

def test_no_hidden_finite_lookup():
    rr=ag.public_features(ag.public_sentences(sentence(['amatur','abc']),{},'a'))
    assert not any('finite:confidence=' in f for r in rr for f in r['features'])

def test_anchor_inventory_uses_supplied_fit_only():
    ss=sentence(['in']*5+['rare']*4+['content']*7)
    for t in ss[0]['tokens']:
        if t['word'] in ('in','rare'):t['pos']='ADP'
    assert ag.anchor_inventory(ss)=={'in':'ADP'}

def test_anchor_override_leaves_hidden_predictions_unchanged():
    rows=[{'anchor_tag':'ADP'},{'anchor_tag':'X'}];q=ag.anchor_override(rows,[[.2,.8],[.3,.7]],['ADP','NOUN'])
    assert np.allclose(q,[[1,0],[.3,.7]])

def test_pooling_does_not_use_id_value():
    rows=[{'word':'a'},{'word':'b'},{'word':'a'}];other=[{'word':'z'},{'word':'q'},{'word':'z'}];p=np.array([[1.,0],[0,1],[.2,.8]])
    assert np.allclose(ag.pool(rows,p),ag.pool(other,p))

def test_fold_local_pool_cannot_reimport_other_fold_predictions():
    a='1';b=next(str(i) for i in range(2,100) if fold(str(i))!=fold(a));rows=[dict(sid=a,word='x'),dict(sid=b,word='x')];q=np.array([[1.,0],[0,1]])
    assert np.allclose(fold_pool(rows,q),q)
    assert not np.allclose(ag.pool(rows,q),q)
