from copy import deepcopy
import numpy as np
from voynich_smt.occurrence_case import context,fit,predict


def token(lemma,pos,head,rel,features=None):
    return dict(lemma=lemma,pos=pos,head=head,rel=rel,features=features or {})


def sentence():
    return [token('mitto','VERB',None,'root',{'Mood':'Ind','Tense':'Pres','Case':'Acc'}),token('urbs','NOUN',0,'obl',{'Case':'Acc'}),token('in','ADP',1,'case'),token('magnus','ADJ',1,'amod',{'Case':'Acc'}),token('nunc','ADV',0,'advmod')]


def test_target_phrase_lexical_and_morphological_mutation_has_no_effect():
    tokens=sentence();expected=context(tokens,1,0);altered=deepcopy(tokens)
    for i in (1,2,3):altered[i].update(lemma='arbitrary',pos='X',features={'Case':'Abl','Number':'Plur','Gender':'Fem'})
    assert context(altered,1,0)==expected
    assert all('urbs' not in k and 'magnus' not in k and 'Case' not in k for k in expected)


def test_case_number_and_gender_anywhere_are_ignored():
    tokens=sentence();expected=context(tokens,1,0)
    for t in tokens:t['features'].update(Case='Abl',Number='Plur',Gender='Fem')
    assert context(tokens,1,0)==expected


def test_real_non_target_occurrence_context_can_change_features():
    tokens=sentence();a=context(tokens,1,0);tokens[4]['lemma']='ibi';b=context(tokens,1,0)
    assert a!=b and a['child:advmod:nunc']==1 and b['child:advmod:ibi']==1


def test_cycles_and_predicates_inside_target_subtree_terminate_safely():
    tokens=sentence();tokens[0]['head']=1
    assert context(tokens,1,0)=={'bias':1.}
    assert context(tokens,1,None)=={'bias':1.}


def test_context_model_learns_repeated_source_signal_with_source_vocabulary():
    records=[dict(sent_id=str(i),predicate='v',case='Acc' if i%2 else 'Abl') for i in range(20)];features=[{'bias':1.,'cue':float(i%2)} for i in range(20)];model=fit(records,features)
    a,b=predict(model,[{'bias':1.,'cue':0.},{'bias':1.,'cue':1.}],['v','v'])
    assert a<.5<b
    assert predict(model,[{'bias':1.,'cue':1.,'target_only':99}],['v'])==[b]
    assert np.isfinite(model['objective'])


def test_calibration_control_cannot_use_occurrence_cue():
    records=[dict(sent_id=str(i),predicate='v',case='Acc' if i%2 else 'Abl') for i in range(10)];features=[{'bias':1.,'cue':float(i%2)} for i in range(10)];model=fit(records,features,'calibration')
    assert model['vocabulary']==['bias']
    a,b=predict(model,[{'bias':1.,'cue':0.},{'bias':1.,'cue':1.}],['v','v'])
    assert a==b
