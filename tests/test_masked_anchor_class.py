from voynich_smt.masked_anchor_class import masked_type_features,cap_rows,type_fold,type_summary
from voynich_smt import anchor_grammar as ag


def test_whole_type_and_all_held_types_hidden(monkeypatch):
    public=[dict(sent_id='s',tokens=[dict(id='a',anchor='target',tag='ADP'),dict(id='h',anchor='held',tag='CCONJ'),dict(id='z',anchor='safe',tag='DET'),dict(id='a',anchor='target',tag='ADP')])]
    original=ag.public_features;captured=[]
    def capture(masked):
        captured.extend(masked)
        return original(masked)
    monkeypatch.setattr(ag,'public_features',capture)
    rows=masked_type_features(public,{'h'},'a')
    assert len(rows)==2
    assert [t['anchor'] for t in captured[0]['tokens']]==[None,None,'safe',None]
    assert all(r['anchor_tag']=='X' for r in rows)
    assert public[0]['tokens'][0]['anchor']=='target'
    assert all('target' not in f and 'held' not in f for r in rows for f in r['features'])


def test_row_cap_is_deterministic_and_type_metrics_not_token_weighted():
    rows=[dict(sid='s',index=i) for i in range(40)]
    assert cap_rows(rows)==cap_rows(list(reversed(rows)))
    assert len(cap_rows(rows))==20
    assert type_fold('et')==type_fold('et')
    records=[dict(n=1000,sentences=10,gold=0,probabilities={'context':[.9,.1]}),dict(n=2,sentences=1,gold=1,probabilities={'context':[.9,.1]})]
    result=type_summary(records,'context')
    assert result['all']['accuracy']==.5
    assert result['supported']['accuracy']==1
