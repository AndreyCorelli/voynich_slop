import numpy as np
from voynich_smt.candidate_expansion import propose,expand


def test_word_cap_aggregates_only_flagged_occurrences():
    support=np.array([[1,0],[0,1],[0,0]],bool);ids=[0,0,0,1];p=np.array([[.1,.7,.2],[.05,.3,.65],[0,0,1],[0,0,1]]);flagged=[1,1,0,0]
    a=propose(support,ids,p,flagged,1);assert a=={'0':[1]}
    b=propose(support,ids,p,flagged,2);assert b=={'0':[1,2]}
    changed=p.copy();changed[2:]=[1.,0,0];assert propose(support,ids,changed,flagged,2)==b
    mask=expand(support,b);assert np.all(mask[support]);assert (mask&~support).sum()==2 and not mask[0,1]


def test_context_and_random_add_identical_counts_to_identical_words():
    support=np.array([[1,0,1],[0,1,1],[0,0,1],[0,0,1]],bool);ids=[0,1,2];p=np.ones((3,4))*.25;flagged=[1,1,1]
    context=propose(support,ids,p,flagged,2);random=propose(support,ids,p,flagged,2,'random',7)
    assert context.keys()==random.keys()=={'0','1'}
    assert all(len(context[w])==len(random[w])==2 for w in context)
    assert random==propose(support,ids,p,flagged,2,'random',7)
    for additions in (context,random):
        for w,cc in additions.items():assert not support[cc,int(w)].any() and len(set(cc))==len(cc)


def test_condition_outside_before_equal_occurrence_averaging():
    support=np.array([[1],[0],[0]],bool);p=np.array([[.01,.8,.19],[.9,0,.1]])
    # Conditional means favor class2; raw sums would favor class1.
    assert propose(support,[0,0],p,[1,1],1)=={'0':[2]}
    assert propose(support,[0,0],p,[0,0],2)=={}


def test_expansion_does_not_restrict_existing_candidates():
    support=np.eye(3,dtype=bool);result=expand(support,{'0':[1,2],'1':[2]})
    np.testing.assert_array_equal(result.sum(axis=0),[3,2,1]);assert np.all(result[support])
