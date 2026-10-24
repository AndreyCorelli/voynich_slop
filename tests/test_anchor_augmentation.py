from benchmarks.grammar_anchor_augmentation_iteration89 import robust_policy


def rows(invert=False):
    return [dict(word=str(i),labels={'pp':i<20},scores={'pooled_pos':{'pp':(.9 if i<20 else .2) if not invert else (.2 if i<20 else .9)}}) for i in range(40)]


def test_robust_policy_uses_all_patterns_and_support():
    selected,curve=robust_policy({'correct':rows(),'error':rows()},10)
    assert selected['threshold']==.9
    assert all(v['precision']==1 for v in selected['stats'].values())
    failed,_=robust_policy({'correct':rows(),'error':rows(True)},10)
    assert failed is None
    failed,_=robust_policy({'correct':rows(),'error':rows()},21)
    assert failed is None
    assert len(curve)==101
