from voynich_smt.repair_budget_selection import edit_counts,select_budget


def test_spoil_constraint_and_ties_prefer_less_damage():
    old=[0,0,0,0];gold=[0,0,1,1]
    record=dict(baseline=old,gold=gold,predictions={0.:old,.001:[0,0,1,0],.01:[1,0,1,1],.1:[0,1,1,1]})
    for risk in (0.,.5,1.):
        p=select_budget([record],risk);assert p['budget']==.001 and p['calibration']['spoiled']==0 and p['calibration']['net']==1


def test_higher_net_gain_is_selected_only_if_feasible():
    r=dict(baseline=[0,0,0,0,0,0],gold=[0,0,0,1,1,1],predictions={0.:[0]*6,.01:[0,0,0,1,0,0],.1:[1,0,0,1,1,1]})
    assert select_budget([r],0.)['budget']==.01
    assert select_budget([r],.34)['budget']==.1


def test_zero_update_wins_without_positive_gain():
    r=dict(baseline=[0,1],gold=[0,1],predictions={'0.0':[0,1],'.01':[0,1],'.1':[1,1]})
    p=select_budget([r],1.);assert p['budget']==0 and p['calibration']['net']==0


def test_pooling_and_correction_accounting():
    c=edit_counts([0,1,0],[1,0,1],[1,1,1]);assert c==dict(tokens=3,baseline_correct=1,corrected=2,spoiled=1,net=1)
    r=dict(baseline=[0,0],gold=[0,1],predictions={0.:[0,0],.1:[0,1]});p=select_budget([r,r],0.)
    assert p['calibration']['tokens']==4 and p['calibration']['net']==2 and p['budget']==.1
