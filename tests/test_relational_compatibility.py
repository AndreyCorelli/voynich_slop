from copy import deepcopy
from voynich_smt.construction_interventions import morphology,domains,lattice
from voynich_smt.relational_compatibility import role_witness,pp_lattice,sv_morphology,sv_domains,sv_lattice,sv_summary


def token(word,pos,case='',number='',person='',gender='',form=''):
    return dict(word=word,pos=pos,features=dict(Case=case,Number=number,Person=person,Gender=gender,VerbForm=form))


def test_genitive_dependent_has_own_number_gender():
    tokens=[token('in','ADP'),token('istorum','DET','Gen','Plur',gender='Masc'),token('sella','NOUN','Abl','Sing',gender='Fem')];lex=morphology([tokens]);reference=dict(left=0,right=2,head=2,predicate=None);d=domains(tokens,0,reference);candidate=[0,2,2,'Abl',None]
    assert candidate not in lattice(tokens,0,d,lex)[0]
    assert candidate in pp_lattice(tokens,0,d,lex)
    assert role_witness(tokens,0,2,2,'Abl',lex)['roles']['1']==['genitive_dependent']


def test_role_alternative_does_not_license_arbitrary_disagreement():
    tokens=[token('in','ADP'),token('magnos','ADJ','Acc','Plur',gender='Masc'),token('sella','NOUN','Abl','Sing',gender='Fem')]
    assert role_witness(tokens,0,2,2,'Abl',morphology([tokens])) is None


def test_agreement_connects_subject_and_predicate_identity():
    tokens=[token('puella','NOUN','Nom','Sing'),token('puellae','NOUN','Nom','Plur'),token('uenit','VERB',number='Sing',person='3',form='Fin'),token('ueniunt','VERB',number='Plur',person='3',form='Fin')];d=sv_domains(tokens,sv_morphology([tokens]));raw=sv_lattice(d,'none');agreed=sv_lattice(d,'agreement');ref=[0,2,'Sing','3','Sing','3']
    assert sv_summary(raw,ref,('subject',))['choices']['predicate']==2
    assert sv_summary(agreed,ref,('subject',))['unrevealed_resolved']['predicate']
    assert sv_summary(agreed,ref,('predicate',))['unrevealed_resolved']['subject']


def test_person_adds_information_beyond_number():
    tokens=[token('ego','PRON','Nom','Sing','1'),token('uenio','VERB',number='Sing',person='1',form='Fin'),token('uenit','VERB',number='Sing',person='3',form='Fin')];d=sv_domains(tokens,sv_morphology([tokens]));ref=[0,1,'Sing','1','Sing','1']
    assert sv_summary(sv_lattice(d,'number'),ref)['links']==2
    assert sv_summary(sv_lattice(d,'agreement'),ref)['unique_link_correct']


def test_hidden_features_remove_identity_discrimination_and_reference_mismatch_is_visible():
    tokens=[token('puella','NOUN','Nom','Sing'),token('ueniunt','VERB',number='Plur',person='3',form='Fin')];lex=sv_morphology([tokens]);ref=[0,1,'Sing','3','Plur','3']
    assert ref in sv_lattice(sv_domains(tokens,lex),'none')
    assert not sv_summary(sv_lattice(sv_domains(tokens,lex),'agreement'),ref)['reference_retained']
    assert sv_lattice(sv_domains(tokens,lex,True),'hidden')


def test_word_type_filter_does_not_read_reference_edges_or_occurrence_features():
    tokens=[token('puella','NOUN','Nom','Sing'),token('uenit','VERB',number='Sing',person='3',form='Fin')];lex=sv_morphology([tokens]);expected=sv_domains(tokens,lex);altered=deepcopy(tokens)
    for t in altered:t.update(head=99,rel='wrong',features={'Case':'Acc','Number':'Plur'})
    assert sv_domains(altered,lex)==expected
