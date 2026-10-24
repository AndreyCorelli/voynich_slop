from voynich_smt.adp_confidence_gate import assignments,choose


def test_uncertain_adp_is_unknown_without_flipping_or_changing_conjunctions():
    p={'low':.49,'high':.1,'conj':.51}
    assert assignments(p,.6)=={'high':'ADP','conj':'CCONJ'}
    assert assignments(p,None)=={'low':'ADP','high':'ADP','conj':'CCONJ'}


def test_selector_does_not_trade_away_coverage_to_claim_precision():
    rows=[dict(threshold=0.,metrics=dict(tp=100,fp=20,precision=100/120)),dict(threshold=.6,metrics=dict(tp=79,fp=0,precision=1.)),dict(threshold=.7,metrics=dict(tp=80,fp=5,precision=80/85))]
    assert choose(rows)['threshold']==.7
    assert choose(rows[:2])==dict(threshold=None,qualified=False)
