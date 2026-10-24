from voynich_smt.combined_repair_gate import calibrate,select


def cases():
    rows=[]
    for regime,n in [('full',12),('sparse',24)]:
        good=dict(pair=['a','b'],gain=2.,gap=.5,stability=.9)
        ref=dict(pair=['a','b'],error=True,supported=True)
        rows.extend(dict(regime=regime,features=dict(good),reference=dict(ref)) for _ in range(n))
        for gap,stability in [(.5,.6),(.05,.95)]:
            rows.append(dict(regime=regime,features=dict(good,gap=gap,stability=stability),reference=dict(ref,pair=['c','d'])))
    return rows


def test_joint_gate_separates_errors_that_each_two_component_gate_cannot():
    chosen,_=calibrate(cases())
    assert chosen['qualified']
    assert chosen['policy']==dict(threshold=2.,gap=.1,stability=.75)
    assert chosen['stats']['full']['hit']==12 and chosen['stats']['sparse']['hit']==24
    assert sum(s['wrong'] for s in chosen['stats'].values())==0


def test_clean_control_guard_still_forces_off_despite_high_precision():
    rows=cases();rows.append(dict(regime='full',features=dict(pair=['a','b'],gain=2.,gap=.5,stability=.9),reference=dict(pair=None,error=False,supported=False)))
    chosen,_=calibrate(rows)
    assert chosen['policy']['threshold'] is None
    assert select(rows[0]['features'],chosen['policy']) is None
