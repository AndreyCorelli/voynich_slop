from voynich_smt.anchor_thresholds import exact_policy


def rec(name,score,wrong,n=100):
    return dict(anchor_id=name,disagreement=score,class_wrong=wrong,n=n,supported=True)


def test_exact_cutoff_recovers_coarse_grid_gap_without_relaxing_guards():
    clean=[rec('a',-.2,False),rec('b',.273,False)]
    corrupted=[rec('a',.469,True),rec('b',.021,True)]
    chosen,curve=exact_policy(clean,corrupted)
    assert chosen['threshold']==.469
    assert chosen['clean']['fp']==0 and chosen['corrupted']['tp']==1
    assert any(r['threshold'] is None for r in curve)
    failed,_=exact_policy([rec('x',2,False)],[rec('x',1,True)])
    assert failed['threshold'] is None
