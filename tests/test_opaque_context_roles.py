import numpy as np
from voynich_smt.opaque_context_roles import statistics


def dense_reference(ids,w):
    vocab=sorted(set(ids));ix={v:i for i,v in enumerate(vocab)};f=np.zeros((len(vocab),len(vocab)))
    for a,b in zip(ids,ids[1:]):f[ix[a],ix[b]]+=1
    left=f.T/np.maximum(f.T.sum(axis=1,keepdims=True),1);right=f/np.maximum(f.sum(axis=1,keepdims=True),1);q=np.concatenate([left,right],axis=1);a=left[ix[w]]@q;b=right[ix[w]]@q
    return np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)) if np.linalg.norm(a)*np.linalg.norm(b) else 0.


def test_sparse_similarity_matches_independent_dense_calculation():
    ids=list('axbacybxazbacx')
    for w,r in statistics(ids,set(ids)).items():assert abs(r['role_similarity']-dense_reference(ids,w))<1e-12


def test_arbitrary_id_renaming_and_direction_reversal():
    ids=list('axbacybxazbacx');rename={w:str(100-i) for i,w in enumerate(sorted(set(ids)))};a=statistics(ids,set(ids));b=statistics([rename[w] for w in ids],set(rename.values()));rev=statistics(ids[::-1],set(ids))
    for w in a:
        assert abs(a[w]['role_similarity']-b[rename[w]]['role_similarity'])<1e-12
        assert abs(a[w]['role_similarity']-rev[w]['role_similarity'])<1e-12


def test_empty_singleton_and_missing_candidates():
    assert statistics([],{'x'})=={}
    assert statistics(['x'],{'x','missing'})=={'x':dict(n=1,supported=False,role_similarity=0.)}
