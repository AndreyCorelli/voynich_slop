from voynich_smt.joint_unit_oracle_v2 import context,subject_values,reasons


def token(pos,head,rel,**features):return dict(pos=pos,head=head,rel=rel,features=features)


def test_coordination_preserves_unknown_morphology():
    tokens=[token('PRON',3,'nsubj'),token('PRON',0,'conj',Person='1'),token('AUX',3,'cop',Number='Sing',Person='3'),token('ADJ',None,'root',Number='Sing')];ctx=context(tokens)
    for feature in ('Number','Person','Gender'):assert subject_values(tokens,0,feature,ctx,True)==set()
    frame=dict(subject=0,carrier=2)
    assert reasons(frame,(3,'cop'),tokens,ctx,dict(sv='coord',adjective='coord'),{0})==[]


def test_permissive_coordination_never_adds_rejection_reasons():
    for snumber in ('','Sing','Plur'):
        for vnumber in ('','Sing','Plur'):
            for sperson in ('','1','2','3'):
                tokens=[token('PRON',3,'nsubj',Number=snumber,Person=sperson,Gender='Fem',Case='Nom'),token('NOUN',0,'conj',Number='Sing',Gender='Masc'),token('AUX',3,'cop',Number=vnumber,Person='3'),token('ADJ',None,'root',Number=vnumber,Gender='Masc',Case='Nom')];ctx=context(tokens);frame=dict(subject=0,carrier=2)
                strict=set(reasons(frame,(3,'cop'),tokens,ctx,dict(sv='strict',adjective='strict'),{0}));permissive=set(reasons(frame,(3,'cop'),tokens,ctx,dict(sv='coord',adjective='coord'),{0}))
                assert permissive<=strict
