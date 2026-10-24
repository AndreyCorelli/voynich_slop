from benchmarks.grammar_joint_subject_none_iteration65_control import exact_thresholds,count_metrics


def test_exact_threshold_sweep_matches_exhaustive_counts_with_tied_margins_and_unit_abstention():
    points=[dict(margin=.1,carrier_correct=True,unit_correct=True,unit_emitted=True),dict(margin=.1,carrier_correct=False,unit_correct=False,unit_emitted=False),dict(margin=1.,carrier_correct=True,unit_correct=False,unit_emitted=True),dict(margin=2.,carrier_correct=False,unit_correct=False,unit_emitted=True)]
    result=exact_thresholds(points,3,-1)
    for row in result['grid']:
        accepted=[p for p in points if p['margin']>row['cutoff']+1e-10]
        assert row['carrier']==count_metrics(sum(p['carrier_correct'] for p in accepted),len(accepted),3)
        assert row['unit']==count_metrics(sum(p['unit_correct'] for p in accepted),sum(p['unit_emitted'] for p in accepted),3)
    assert -1 in [r['cutoff'] for r in result['grid']]


def test_empty_calibration_predictions_are_supported():
    result=exact_thresholds([],2,-1.)
    assert result['selected']['unit']['unit']['predicted']==0
