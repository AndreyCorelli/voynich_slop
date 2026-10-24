import json
from dataclasses import asdict
import pytest
from benchmarks import training_diversity as b
from voynich_smt.data.corpus import digest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.recovery import Recovery


def test_selection_is_corpus_order_disjoint_and_nested():
    records=[{'tokens':list(w),'excluded_reason':reason} for w,reason in
             [('cc',None),('bb',None),('dd','excluded'),('ee',None),('bb',None),('ff',None)]]
    dictionary=WordDictionary.from_strings(('aa','bb','cc','dd','ff'))
    types,provenance=b.select_types([tuple('aa')],[tuple('cc')],dictionary,records,3)
    assert types==list(map(tuple,('aa','bb','ff')))
    assert [p['record_index'] for p in provenance]==[1,5]
    short,_=b.select_types([tuple('aa')],[tuple('cc')],dictionary,records,2)
    assert types[:2]==short
    with pytest.raises(ValueError,match='Insufficient'):b.select_types([tuple('aa')],[tuple('cc')],dictionary,records,4)


def test_only_lengths_supplied_unknown_unscored_and_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def spy(lengths,q):
        received.append((lengths,q));return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b.lengths,'solve',spy)
    r=b.run();p=json.loads((tmp_path/'prepared.json').read_text())
    for (lengths,q),case in zip(received,p['cases']):
        assert lengths==tuple(case['revealed_lengths'])
        assert digest(asdict(q))==digest(case['request']) and q.timeout_ms==5000
        assert len(q.ciphertext.words)==2*case['distinct_training_types']
    assert len(p['reused_baselines'])==2 and len(received)==4
    assert all(row['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in row for row in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==4
    b.validate()
