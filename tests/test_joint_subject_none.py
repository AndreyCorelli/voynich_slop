from itertools import product
import numpy as np
import pytest
from voynich_smt.joint_subject_none import decode,independent


def frame(s,vs,scores):return dict(subject=s,predicates=vs,scores=scores)


def test_zero_penalty_reproduces_threshold_ties_and_none():
    frames=[frame(0,[3,4],[1,0]),frame(1,[3,4],[1,1]),frame(2,[3],[-1]),frame(5,[],[])]
    assert decode(frames,0,0)[0]=={0:3,1:None,2:None,5:None}


def test_competition_can_choose_none_or_an_alternative_carrier():
    frames=[frame(0,[3,4],[3,0]),frame(1,[3,4],[2,1.5])]
    assert decode(frames,0,0)[0]=={0:3,1:3}
    assert decode(frames,0,1)[0]=={0:3,1:4}
    assert decode([frame(0,[3],[3]),frame(1,[3],[.5])],0,1)[0]=={0:3,1:None}


def test_soft_penalty_keeps_multiple_strong_subjects():
    assert decode([frame(0,[3],[4]),frame(1,[3],[3])],0,1)[0]=={0:3,1:3}


def test_tied_global_optima_abstain_for_ambiguous_subjects():
    prediction,stats=decode([frame(0,[3],[1]),frame(1,[3],[1])],0,2)
    assert prediction=={0:None,1:None} and stats['ambiguous_subjects']==1


def test_lp_predictions_are_exactly_attachments_shared_by_all_exhaustive_optima():
    rng=np.random.default_rng(65)
    for _ in range(20):
        frames=[frame(s,[5,6],(rng.random(2)*3+.1).tolist()) for s in range(3)];penalty=float(rng.choice([.25,1.,2.]));_,edges=independent(frames,0);possibilities=[]
        for assignment in product((None,5,6),repeat=3):
            total=sum(next(u for s,v,u in edges if s==i and v==value) for i,value in enumerate(assignment) if value is not None);n=sum(v is not None for v in assignment);used=len({v for v in assignment if v is not None});possibilities.append((total-penalty*(n-used),assignment))
        maximum=max(v for v,_ in possibilities);opt=[a for v,a in possibilities if abs(v-maximum)<=1e-8];expected={s:opt[0][s] if all(a[s]==opt[0][s] for a in opt) else None for s in range(3)}
        assert decode(frames,0,penalty)[0]==expected


def test_negative_penalty_is_rejected():
    with pytest.raises(ValueError):decode([],0,-1)
