from voynich_smt.omission_aware_gate import calibrate


def row(case,regime,reference_pair=None):
    return dict(case=case,regime=regime,features=dict(pair=['a','b'],gain=1.,gap=.5,stability=.9),reference=dict(pair=['a','b'] if reference_pair is None else reference_pair,error=True,supported=True))


def test_repeated_views_cannot_fake_distinct_original_case_coverage():
    cases=[row(str(i),'complete') for i in range(20)]+[row('one','omission') for _ in range(100)]
    chosen,_=calibrate(cases);assert chosen['policy']['threshold'] is None


def test_unavailable_wrong_calls_force_off_even_with_ample_coverage():
    cases=[row(str(i),'complete') for i in range(20)]+[row(str(i),'omission') for i in range(20)]
    chosen,_=calibrate(cases);assert chosen['qualified']
    bad=row('missing','omission',['x','y']);bad['reference']['supported']=False;cases.append(bad)
    chosen,_=calibrate(cases);assert chosen['policy']['threshold'] is None
