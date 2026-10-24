from itertools import product
import numpy as np
from voynich_smt.joint_unit_oracle import context,coordination,reasons,allowed_indices,decode,shared_gold_conflicts,compatible,subject_values


def token(pos,head,rel,**features):return dict(pos=pos,head=head,rel=rel,features=features)


def frame(s,v,options,scores,gold=None):return dict(subject=s,carrier=v,options=options,scores=np.asarray(scores,dtype=float),gold=gold)


def test_shared_decoder_matches_exhaustive_score_maximum():
    options=[(4,'direct'),(2,'cop'),(3,'cop')]
    frames=[frame(0,4,options,[1,4,0]),frame(1,4,options,[1,0,5])];allowed={0:[0,1,2],1:[0,1,2]}
    independent,_=decode(frames,allowed);joint,stats=decode(frames,allowed,True)
    assert independent[0][1]==2 and independent[1][1]==3
    assert joint[0][1]==joint[1][1]==3 and stats['multiple_frame_groups']==1
    possible=[(sum(frames[i]['scores'][j] for i,j in enumerate(js)),js) for js in product(range(3),repeat=2) if options[js[0]]==options[js[1]]]
    assert max(possible)[0]==5


def test_shared_decoder_intersects_domains_and_abstains_on_empty_or_tie():
    a=frame(0,4,[(4,'direct'),(2,'cop')],[0,2]);b=frame(1,4,[(4,'direct'),(2,'cop')],[2,0]);frames=[a,b]
    output,stats=decode(frames,{0:[0,1],1:[0,1]},True);assert output=={0:None,1:None} and stats['tied_groups']==1
    output,stats=decode(frames,{0:[0],1:[1]},True);assert output=={0:None,1:None} and stats['empty_groups']==1


def test_decoder_does_not_read_gold_labels_and_keeps_carrier_groups_separate():
    a=frame(0,3,[(3,'direct'),(2,'cop')],[1,2],gold=[0,3,3,'direct']);b=frame(1,4,[(4,'direct'),(2,'cop')],[3,0])
    output,_=decode([a,b],{0:[0,1],1:[0,1]},True)
    a['gold']=['wrong'];assert decode([a,b],{0:[0,1],1:[0,1]},True)[0]==output
    assert output=={0:[0,2,3,'cop'],1:[1,4,4,'direct']}


def test_scope_allows_subject_role_in_another_clause():
    tokens=[token('NOUN',2,'nsubj'),token('AUX',2,'cop'),token('NOUN',None,'root'),token('PRON',4,'nsubj'),token('VERB',2,'acl')]
    ctx=context(tokens);r=frame(0,1,[(3,'cop')],[1])
    assert reasons(r,(3,'cop'),tokens,ctx,dict(roles='assigned_global'),{0,3})==['role_reuse']
    assert reasons(r,(3,'cop'),tokens,ctx,dict(roles='assigned_clause'),{0,3})==[]


def test_roles_and_shared_decoder_need_no_annotation_when_global():
    frames=[frame(0,3,[(3,'direct'),(1,'cop')],[0,3]),frame(1,3,[(3,'direct'),(2,'cop')],[0,2])]
    domains=allowed_indices(frames,[],None,dict(roles='assigned_global',shared=True))
    assert domains[0]==[0] and domains[1]==[0,1]
    output,_=decode(frames,domains,True);assert output[0][3]==output[1][3]=='direct'


def test_coordination_permissive_number_retains_plural_and_singular():
    tokens=[token('NOUN',3,'nsubj',Number='Sing',Gender='Fem'),token('NOUN',0,'conj',Number='Sing',Gender='Masc'),token('AUX',3,'cop',Number='Plur'),token('ADJ',None,'root',Number='Plur',Gender='Masc')]
    ctx=context(tokens);assert coordination(tokens,0)=={0,1}
    r=frame(0,2,[(3,'cop')],[1])
    assert 'sv_Number' in reasons(r,(3,'cop'),tokens,ctx,dict(sv='strict'),{0})
    assert reasons(r,(3,'cop'),tokens,ctx,dict(sv='coord',adjective='coord'),{0})==[]
    assert subject_values(tokens,0,'Number',ctx,True)=={'Sing','Plur'}


def test_unknown_morphology_does_not_exclude_and_predicate_nouns_need_no_gender_agreement():
    tokens=[token('NOUN',2,'nsubj',Gender='Fem'),token('AUX',2,'cop'),token('NOUN',None,'root',Gender='Masc')];ctx=context(tokens);r=frame(0,1,[(2,'cop')],[1])
    assert compatible(set(),{'Sing'})
    assert reasons(r,(2,'cop'),tokens,ctx,dict(sv='strict',adjective='strict'),{0})==[]


def test_strict_adjective_mismatch_and_shared_gold_conflicts_are_reported():
    tokens=[token('NOUN',2,'nsubj',Number='Sing'),token('AUX',2,'cop'),token('ADJ',None,'root',Number='Plur')];ctx=context(tokens);r=frame(0,1,[(2,'cop')],[1],[0,2,1,'cop'])
    assert reasons(r,(2,'cop'),tokens,ctx,dict(adjective='strict'),{0})==['adjective_Number']
    b=frame(3,1,[(4,'cop')],[1],[3,4,1,'cop']);assert shared_gold_conflicts([r,b])[0]['reason']=='different_gold_heads_or_types'
