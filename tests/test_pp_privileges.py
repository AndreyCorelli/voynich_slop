from copy import deepcopy
from benchmarks.grammar_pp_privileges_iteration83 import rows83

def fixture():
    tokens=[dict(word='in',pos='ADP',features={},rel='case',head=1),dict(word='urbe',pos='NOUN',features={'Case':'Abl'},rel='obl',head=None),dict(word='x',pos='ADV',features={},rel='advmod',head=1)]
    pm={'words':{'in':{'ADP':3},'urbe':{'NOUN':3},'x':{'ADV':3}},'prior':{'ADP':3,'NOUN':3,'ADV':3}}
    return [{'sent_id':'a','tokens':tokens}],pm

def test_all_tokens_not_filtered_by_pos_or_case():
    ss,pm=fixture();rr=rows83(ss,pm,{},{});assert len(rr)==3
    assert sum(r['matched'] for r in rr)==1
    assert rr[1]['structure_gold']>=4 and rr[0]['structure_gold']<4

def test_reference_annotations_cannot_change_features():
    ss,pm=fixture();a=rows83(ss,pm,{},{});changed=deepcopy(ss)
    for t in changed[0]['tokens']:t.update(pos='X',features={},head=None,rel='root')
    b=rows83(changed,pm,{},{})
    assert len(a)==len(b)
    for x,y in zip(a,b):
        assert x['masked_center']==y['masked_center'] and x['predicted_pos']==y['predicted_pos']

def test_supplied_pos_feature_absent():
    ss,pm=fixture();rr=rows83(ss,pm,{},{})
    assert not any('suppliedCenterPOS' in f for r in rr for f in r['predicted_pos'])
    assert not any('CenterPOS' in f for r in rr for f in r['masked_center'])

def test_predicted_center_pos_follows_model_not_reference():
    ss,pm=fixture();ss[0]['tokens'][1]['pos']='ADJ';rr=rows83(ss,pm,{},{})
    assert 'predictedCenterPOS:NOUN' in rr[1]['predicted_pos']
