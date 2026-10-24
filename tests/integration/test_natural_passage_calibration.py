from dataclasses import asdict
import pytest
from benchmarks import natural_passage_calibration as b
from voynich_smt.data.corpus import digest
from voynich_smt.solver.recovery import Recovery


def test_selection_contiguous_no_barrier_skip_and_coverage(monkeypatch):
    monkeypatch.setattr(b,'TRAIN',3);monkeypatch.setattr(b,'HELD',3)
    words=('ab','ba','aa','aba','bab','bba')
    records=[{'tokens':[],'excluded_reason':None} for _ in range(8)]+[{'tokens':list(w),'excluded_reason':None} for w in words]
    allowed=set(map(tuple,words))
    start,train,held,block=b.select_passage(records,allowed)
    assert start==8 and block==records[8:14]
    assert train.words==tuple(map(tuple,words[:3])) and held.words==tuple(map(tuple,words[3:]))
    records[10]['excluded_reason']='barrier'
    with pytest.raises(ValueError,match='No eligible'):b.select_passage(records,allowed)
    records[10]['excluded_reason']=None;records[13]['tokens']=list('ca');allowed.add(tuple('ca'))
    with pytest.raises(ValueError,match='No eligible'):b.select_passage(records,allowed)


def test_matched_solver_inputs_frozen_passages_and_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);known=[];hidden=[]
    def known_spy(plain,q):
        known.append((plain,q));return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    def hidden_spy(q):
        hidden.append(q);return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b,'known_solve',known_spy);monkeypatch.setattr(b,'recover_observed_codes',hidden_spy)
    r=b.run();p=b.prepare()
    assert len(known)==4 and len(hidden)==8 and not p['unavailable']
    for plain,q in known:
        case=next(c for c in p['cases'] if digest(c['request'])==digest(asdict(q)))
        assert case['kind']=='positive' and digest(asdict(plain))==digest(case['truth']['plaintext'])
    assert all(q.timeout_ms==5000 and len(q.dictionary.words)==64 and len(q.ciphertext.words)==24 for q in hidden)
    for passage in p['passages'].values():
        assert passage['held_record_indices'][0]==passage['train_record_indices'][-1]+1
        assert len(passage['source_records'])==30
    assert all(row['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in row for row in r['arms'])
    assert digest(b.run())==digest(r) and len(hidden)==8
    b.validate()
