import numpy as np
from scipy.sparse import csr_matrix
from voynich_smt.contextual_nominative import features,objective,replace_nominal

def test_features_exclude_center_pos():
    assert features(['NOUN','VERB','ADP'],1)==features(['NOUN','X','ADP'],1)

def test_objective_gradient_matches_finite_difference():
    x=csr_matrix([[1.,0,1],[1,1,0],[1,1,1]]);y=np.array([0.,1,1]);w=np.array([.2,-.3,.1]);_,g=objective(w,x,y)
    numeric=[]
    for j in range(3):
        d=np.zeros(3);d[j]=1e-6;numeric.append((objective(w+d,x,y)[0]-objective(w-d,x,y)[0])/2e-6)
    assert np.allclose(g,numeric,atol=1e-7)

def test_soft_nominal_replacement_preserves_role_conditionals():
    labels=[['nsubj',['NOUN','Nom','Sing']],['appos',['NOUN','Nom','Sing']],['obj',['NOUN','Acc','Sing']]]
    q=replace_nominal(labels,[.2,.1,.7],.6)
    assert np.allclose(q,[.4,.2,.4]) and abs(sum(q)-1)<1e-12

def test_nominative_replacement_does_not_force_role():
    labels=[['nsubj',['NOUN','Nom','Sing']],['appos',['NOUN','Nom','Sing']],['obj',['NOUN','Acc','Sing']]]
    assert replace_nominal(labels,[.2,.1,.7],1.)[0]<1
