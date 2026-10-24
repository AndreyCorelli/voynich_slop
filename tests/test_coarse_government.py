import numpy as np
from scipy.sparse import csr_matrix
from voynich_smt.coarse_government import fold,objective,structure_label,sham,case_matrix

def test_sentence_fold_is_stable_and_shared_by_occurrences():
    assert fold('123')==fold('123') and 0<=fold('123')<3

def test_multinomial_gradient_matches_finite_difference():
    x=csr_matrix([[1.,0],[1,1],[0,1]]);y=np.array([0,2,7]);w=np.linspace(-.2,.3,16);_,g=objective(w,x,y)
    numeric=[]
    for j in range(len(w)):
        d=np.zeros_like(w);d[j]=1e-6;numeric.append((objective(w+d,x,y)[0]-objective(w-d,x,y)[0])/2e-6)
    assert np.allclose(g,numeric,atol=1e-7)

def test_joint_label_preserves_membership_and_head_category():
    r=dict(pp_bundle=['oraclePP:present=True'],structure_bundle=['oracleHead:pos=VERB'])
    assert structure_label(r)==4
    r['structure_bundle']=['oracleHead:ROOT'];assert structure_label(r)==7

def test_soft_probabilities_remain_continuous_features():
    x=case_matrix([['bias']],[[.1,.9]],{'bias':0}).toarray()
    assert np.allclose(x,[[1,.1,.9]])

def test_sham_never_moves_probabilities_between_sentences():
    rows=[{'sid':'a'},{'sid':'a'},{'sid':'b'}];q=np.eye(3);s=sham(rows,q,1)
    assert np.allclose(s[2],q[2]) and np.allclose(s[:2].sum(axis=0),q[:2].sum(axis=0))
