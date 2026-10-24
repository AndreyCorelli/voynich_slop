from copy import deepcopy
from voynich_smt.construction_interventions import morphology,domains,lattice,interventions,reveal,summarize


def token(word,pos,case='',number='',gender=''):
    return dict(word=word,pos=pos,features={'Case':case,'Number':number,'Gender':gender})


def test_revealed_predicate_can_make_a_wrong_hypothesis_unique_without_propagation():
    candidates=[[0,1,1,'Acc',2],[0,1,1,'Acc',3]];ref=candidates[0]
    s=summarize(candidates,ref,('predicate',))
    assert s['uniquely_correct'] and all(s['unrevealed_resolved'].values())
    assert reveal(candidates,candidates[1],('predicate',))==[candidates[1]]
    assert summarize([candidates[1]],ref)['false_unique']


def test_boundary_can_resolve_unrevealed_head_and_case():
    candidates=[[0,1,1,'Acc',3],[0,2,2,'Abl',3]];s=summarize(candidates,candidates[0],('boundary',))
    assert s['unrevealed_resolved']['head'] and s['unrevealed_resolved']['case']


def test_missing_reference_is_never_recovered_by_revealing_all_facts():
    wrong=[0,1,1,'Abl',2];ref=[0,1,1,'Acc',2];s=summarize([wrong],ref,('boundary','head','case','predicate'))
    assert not s['reference_retained'] and not s['uniquely_correct'] and s['remaining']==0


def test_morphological_witness_can_prune_a_real_candidate_and_case_mask_restores_it():
    tokens=[token('in','ADP'),token('magna','ADJ','Abl','Sing','Fem'),token('urbem','NOUN','Acc','Sing','Fem'),token('it','VERB')];ref=dict(left=0,right=2,head=2,predicate=3);d=domains(tokens,0,ref);lex=morphology([tokens]);candidate=[0,2,2,'Acc',3]
    full,_=lattice(tokens,0,d,lex);hidden,_=lattice(tokens,0,d,lex,True)
    assert candidate not in full and candidate in hidden


def test_lattice_does_not_use_reference_edges_or_token_specific_morphology():
    tokens=[token('in','ADP'),token('urbe','NOUN','Abl','Sing','Fem'),token('est','VERB')];ref=dict(left=0,right=1,head=1,predicate=2);d=domains(tokens,0,ref);lex=morphology([tokens]);expected=lattice(tokens,0,d,lex);altered=deepcopy(tokens)
    for t in altered:t.update(head=99,rel='bad',features={'Case':'Acc'})
    assert lattice(altered,0,d,lex)==expected


def test_oracle_augmentation_expands_domains_without_labeling_a_correct_candidate():
    tokens=[token('in','ADP')]+[token('x','NOUN','Acc') for _ in range(9)]+[token('it','VERB')];ref=dict(left=0,right=9,head=9,predicate=10);d=domains(tokens,0,ref)
    assert d['oracle_additions']=={'head':True,'boundary':True,'predicate':False}
    assert d['heads'][-1]==9 and [0,9] in d['boundaries']
    assert len(interventions())==16
