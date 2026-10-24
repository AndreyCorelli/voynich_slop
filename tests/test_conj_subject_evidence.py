import numpy as np
from scipy.sparse import csr_matrix
from voynich_smt.conj_subject_evidence import features,objective,probabilities,adjust,fit


def test_binary_gradient_matches_finite_difference():
    x=csr_matrix([[1.,0.],[1.,1.],[0.,2.]]);y=np.asarray([0,1,1]);w=np.asarray([.2,-.3]);_,g=objective(w,x,y)
    for j in range(2):
        d=np.zeros(2);d[j]=1e-6
        assert abs((objective(w+d,x,y)[0]-objective(w-d,x,y)[0])/2e-6-g[j])<1e-7


def test_features_ignore_words_annotations_and_morphology_but_distinguish_marker_direction():
    tokens=[dict(pos=p,word='x',head=0,rel='conj',features={'Case':'Nom'}) for p in ('NOUN','CCONJ','NOUN','VERB')];masked=[dict(t,word='?',head=None,rel='?',features={}) for t in tokens]
    assert features(tokens,2,'context')==features(masked,2,'context')
    assert 'left-nominal-marker:True' in features(tokens,2,'context')
    assert features(tokens,0,'pos')==features(tokens,2,'pos')
    assert features(tokens,0,'context')!=features(tokens,2,'context')


def test_soft_evidence_preserves_carrier_order_and_zero_weight_is_exact():
    tokens=[dict(pos='NOUN')];model=dict(mode='pos',vocabulary={'bias':0},weights=[0.]);frames=[dict(subject=0,predicates=[2,3],scores=[2.,1.],gold=2)]
    assert adjust(frames,tokens,model,0)==frames
    changed=adjust(frames,tokens,model,2)[0];assert np.allclose(np.diff(changed['scores']),[-1.]) and changed['scores'][0]<2.
    assert frames[0]['scores']==[2.,1.]


def test_fit_learns_marker_side_without_using_test_labels():
    tokens=[dict(pos='NOUN',rel='nsubj'),dict(pos='CCONJ',rel='cc'),dict(pos='NOUN',rel='conj'),dict(pos='VERB',rel='root')];model=fit([tokens]*20,'context');p=probabilities(tokens,[0,2],model)
    assert p[1]>p[0] and p[0]<.5<p[1]
