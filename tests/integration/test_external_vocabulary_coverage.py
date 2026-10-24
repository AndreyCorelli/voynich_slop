from collections import Counter
import json
from benchmarks import external_vocabulary_coverage as b
from voynich_smt.data.corpus import digest


def test_normalization_fixed_and_frequency_ties():
    counts,excluded=b.normalize_latin(['jam','iam','via','w','non',None],set('abcdefghiklmnopqrstuvxyz'))
    assert counts[tuple('iam')]==2 and counts[tuple('via')]==1 and excluded['w']==1
    assert b.ranked(Counter({('b',):2,('a',):2,('c',):1}))==[('a',),('b',),('c',)]


def test_unavailable_and_json_roundtrip(monkeypatch):
    monkeypatch.setattr(b,'SIZES',(1,3))
    data={'rankings':{'external-only':[['a'],['b']]},'fixed_passage':{'plaintext':{'words':[['x'],['x']]},'holdout_plaintext':{'words':[['a']]}},'grid_windows':[{'words':[['x'],['x']]}]}
    report=b.calculate({'languages':{'toy':data}})
    assert report['rows'][1]['status']=='UNAVAILABLE'
    assert report['rows'][0]['grid']['admitted_one_oov_windows']==0
    assert digest(report)==digest(json.loads(json.dumps(report)))
