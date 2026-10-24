import math
import numpy as np
from voynich_smt.anchor_class_audit import disagreement,flagged,metrics,choose_threshold
from benchmarks.grammar_anchor_class_audit_iteration91 import class_records
from voynich_smt import anchor_grammar as ag


def record(name,wrong,margin,n=10,supported=True):
    return dict(anchor_id=name,class_wrong=wrong,disagreement=margin,n=n,supported=supported)


def test_class_log_ratio_and_support():
    d,mass=disagreement([.2,.6,.2],['ADP','CCONJ','NOUN'],'ADP')
    assert math.isclose(d,math.log(3),rel_tol=1e-10)
    assert mass==.8
    assert not flagged(record('a',True,8,supported=False),0)
    result=metrics([record('a',True,8,supported=False),record('b',False,2)],1)
    assert (result['tp'],result['fp'],result['unsupported_errors'])==(0,1,1)


def test_calibration_preserves_false_alarm_guard_and_off():
    clean=[record('a',False,-2,100),record('b',False,-2,100)]
    corrupted=[record('a',True,3),record('b',True,2)]
    chosen,_=choose_threshold(clean,corrupted)
    assert chosen['threshold']==2
    assert chosen['corrupted']['tp']==2
    bad=[record('a',False,8,100)]
    chosen,_=choose_threshold(bad,corrupted)
    assert chosen['threshold'] is None


def test_hiding_entire_type_removes_proposed_identity_before_prediction(monkeypatch):
    public=[dict(sent_id=str(i),tokens=[dict(id='a',anchor='WRONG',tag='ADP'),dict(id='b',anchor='et',tag='CCONJ'),dict(id='a',anchor='WRONG',tag='ADP')]) for i in range(3)]
    captured=[]
    def predict(features,model):
        captured.extend(features)
        return np.tile([.1,.7,.2],(len(features),1))
    monkeypatch.setattr(ag,'predict',predict)
    model=dict(pos={'0':{}},pos_classes=['ADP','CCONJ','NOUN'])
    r=class_records(public,{'a':'ADP'},model)[0]
    assert r['n']==6 and r['sentences']==3 and r['supported']
    assert all('WRONG' not in f for row in captured for f in row)
    assert all('centerAnchorTag:X' in row for row in captured)
    assert 'class_wrong' not in r
    # Altering proposed name/tag cannot affect independently hidden context evidence.
    other=[dict(s,tokens=[dict(t,anchor='OTHER',tag='CCONJ') if t['id']=='a' else t for t in s['tokens']]) for s in public]
    rr=class_records(other,{'a':'ADP'},model)[0]
    assert r==rr
