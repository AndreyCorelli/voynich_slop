from voynich_smt.anchor_budget import budgets,precision_lower,conservative_policy

def test_budget_ranking_uses_fit_frequency_and_excludes_pronouns():
    words=['a']*8+['b']*7+['c']*6+['d']*5+['e']*4+['f']*3+['pron']*100
    ss=[{'tokens':[{'word':w} for w in words]}];inventory={w:'ADP' for w in 'abcdef'};inventory['pron']='PRON'
    result=budgets(ss,inventory)
    assert list(result['5'])==list('abcde') and result['0']=={}
    assert 'pron' not in result['6']

def test_precision_lower_handles_empty_and_no_success():
    assert precision_lower(0,0)==0 and precision_lower(0,100)==0

def test_exact_lower_bound_for_all_successes():
    alpha=.05/101
    assert abs(precision_lower(80,80)-alpha**(1/80))<1e-12

def rows(n):return [dict(word=str(i),labels={'pp':True},scores={'m':{'pp':.8}}) for i in range(n)]

def test_conservative_policy_rejects_small_perfect_sample():
    assert conservative_policy(rows(20),'m') is None

def test_conservative_policy_accepts_sufficient_perfect_sample():
    p=conservative_policy(rows(80),'m')
    assert p and p['precision_lower']>=.9 and p['threshold']==.8
