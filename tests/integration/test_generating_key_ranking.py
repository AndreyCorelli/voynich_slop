import json

import pytest

from benchmarks import generating_key_ranking as b


def test_ranking_uses_training_only_and_keeps_first_tie():
    model={'vocabulary':['a','b'],'unigrams':{'a':9,'b':1},'outgoing':{},
           'pairs':[],'alpha':1,'tokens':10}
    candidates=[{'plaintext':{'words':[['b']]},'origin':'generating','exact_words':100},
                {'plaintext':{'words':[['a']]},'origin':'wrong','exact_words':0},
                {'plaintext':{'words':[['a']]},'origin':'generating','exact_words':100}]
    scores,order=b.rank_training(candidates,model)
    assert order==[1,2,0] and scores[1]==scores[2]
    for c in candidates:c['origin']='changed';c['exact_words']=-999
    assert b.rank_training(candidates,model)==(scores,order)


def test_fixed_injected_pool_and_score_reproduction(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    report=b.run()
    source=json.loads((b.SOURCE/'prepared.json').read_text())
    assert report['solver_calls']==0 and report['complete']
    assert len(report['cases'])==2
    for row in report['cases']:
        assert row['candidates'][-1]['origin']=='injected_generating'
        assert row['candidates'][-1]['exact_words']==4
        scores,order=b.rank_training([c['result'] for c in row['candidates']],source['model'])
        assert scores==[c['training_score'] for c in row['candidates']]
        assert order==row['training_rank_order']
        assert row['selected_index']==order[0]
    assert [r['generating_rank'] for r in report['cases']]==[2,1]
    assert [(r['baseline_exact_words'],r['augmented_exact_words']) for r in report['cases']]==[(4,4),(1,4)]
    with pytest.raises(ValueError,match='preserve output'):b.run()
