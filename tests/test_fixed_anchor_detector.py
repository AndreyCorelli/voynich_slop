import math
import numpy as np
from voynich_smt.fixed_anchor_detector import predict_records,ARMS
from voynich_smt import anchor_grammar as ag


def test_single_model_no_id_routing_and_entire_type_hidden(monkeypatch):
    public=[dict(sent_id=str(i),tokens=[dict(id='secret',anchor='in',tag='ADP'),dict(id='other',anchor='et',tag='CCONJ'),dict(id='secret',anchor='in',tag='ADP')]) for i in range(3)]
    captured=[]
    def predict(features,model):
        captured.extend(features)
        assert model is marker
        return np.tile([.8,.2],(len(features),1))
    marker={};models={a:marker for a in ARMS if a!='prior'};models['prior']=[.6,.4]
    monkeypatch.setattr(ag,'predict',predict)
    result=predict_records(public,{'secret':'ADP'},models)
    assert result['context'][0]['n']==6 and result['context'][0]['supported']
    assert all('centerAnchorTag:X' in row for row in captured)
    assert all('anchor1:in' not in row and 'anchor-1:in' not in row for row in captured)
    assert all('class_wrong' not in r for rows in result.values() for r in rows)
    rekey=[dict(s,tokens=[dict(t,id='new') if t['id']=='secret' else t for t in s['tokens']]) for s in public]
    changed=predict_records(rekey,{'new':'CCONJ'},models)
    assert changed['context'][0]['mean']==result['context'][0]['mean']
    assert math.isclose(changed['context'][0]['disagreement'],-result['context'][0]['disagreement'],abs_tol=1e-12)
    assert all('new' not in f and 'secret' not in f for row in captured for f in row)
