from benchmarks.grammar_role_compatibility_iteration70 import compatible,readings,context,mass,posterior

def test_joint_readings_do_not_invent_analysis():
    rr=readings([{'pos':'N','features':[['Case','NOM'],['Number','S']]},{'pos':'N','features':[['Case','ACC'],['Number','P']]}])
    assert not any(compatible(('NOUN','Nom','Plur'),r) for r in rr)

def test_unknown_is_no_evidence():
    m={'labels':[['obj',['NOUN','Acc','Sing']]],'prior':[1.], 'vocab':[], 'likelihood':[[]]}
    assert mass(m,[1.],[])==0

def test_masked_context_excludes_center():
    assert context(['NOUN','VERB','ADP'],1)==context(['NOUN','X','ADP'],1)

def test_union_does_not_double_count_duplicate_readings():
    m={'labels':[['obj',['NOUN','Acc','Sing']]]}
    assert mass(m,[1.],[('NOUN','Acc','Sing')]*2)==1

def test_posterior_normalizes_unseen_context():
    m={'labels':[], 'prior':[.3,.7], 'vocab':['1:NOUN'], 'likelihood':[[.2],[.8]]}
    assert abs(sum(posterior(m,['never-seen']))-1)<1e-12
