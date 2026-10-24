import numpy as np
from voynich_smt.structural_head_evidence import features,objective,probabilities,evidence,infer,calibrate


def test_pair_features_ignore_words_and_all_annotations():
    tokens=[dict(pos=p,word='x',lemma='a',head=2,rel='nsubj',features={'Case':'Nom'}) for p in ('NOUN','SCONJ','ADJ','AUX')]
    masked=[dict(t,word='?',lemma='?',head=None,rel='?',features={}) for t in tokens]
    for mode in ('coarse','context'):
        assert features(tokens,2,3,mode)==features(masked,2,3,mode)
    assert features(tokens,0,3,'context')!=features(tokens,2,3,'context')


def test_weighted_multitask_gradient():
    from scipy.sparse import csr_matrix
    x=csr_matrix([[1.,2.],[0.,1.],[-1.,1.]]);y=np.asarray([[1,0],[0,1],[1,1]]);scale=np.asarray([.2,.3,.5]);w=np.asarray([.1,-.2,.3,.4]);_,g=objective(w,x,y,scale)
    for j in range(4):
        d=np.zeros(4);d[j]=1e-6
        assert abs((objective(w+d,x,y,scale)[0]-objective(w-d,x,y,scale)[0])/2e-6-g[j])<1e-7


def test_reflexive_clause_identity_and_role_independent_evidence():
    tokens=[dict(pos='NOUN'),dict(pos='AUX'),dict(pos='ADJ')];model=dict(mode='coarse',vocabulary={'bias':0},weights=[[0.,0.]])
    p=probabilities(tokens,1,[1,2],model);assert np.allclose(p,[[.5,1.],[.5,.5]])
    options=[(1,'direct'),(2,'cop'),(2,'aux')];cues=evidence(tokens,1,options,model)
    assert np.array_equal(cues[1],cues[2]) and cues[0,1]==0.


def test_zero_evidence_weight_recovers_base_and_soft_cue_can_change_head():
    options=[(3,'direct'),(1,'cop'),(2,'cop')];scores=np.asarray([-2.,1.,.9]);cues=np.log(np.asarray([[1.,1.],[.1,.1],[.9,.9]]))
    assert infer(scores,options,0,3,cues,0,0)==[0,1,3,'cop']
    assert infer(scores,options,0,3,cues,1,0)==[0,2,3,'cop']


def test_calibration_uses_zero_and_prefers_it_when_no_gain():
    options=[(2,'direct'),(1,'cop')];frames=[dict(gold=[0,1,2,'cop'],options=options,scores=np.asarray([0.,1.]),cues=np.zeros((2,2)))]
    for arm in ('phrase','clause','joint'):
        selected=calibrate(frames,arm)['selected'];assert selected['phrase_weight']==selected['clause_weight']==0.
