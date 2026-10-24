from dataclasses import asdict

from benchmarks import single_code_baseline as b
from benchmarks.l3_conflict import verify
from voynich_smt.models.text import Text


def test_nested_requests_change_only_homophone_bound(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    p=b.prepare()
    assert len(p['cases'])==19 and not p['unavailable']
    for case in p['cases']:
        q1=b.request_for(case,1);q2=b.request_for(case,2)
        a=asdict(q1);c=asdict(q2)
        a['bounds']['max_homophones']=2
        assert a==c
        assert q1.bounds.min_code_length==1 and q1.bounds.max_code_length==3
    assert b.digest(p)==b.digest(b.prepare())


def test_new_h1_positives_fit_both_models_with_coverage(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare()
    positives=[c for c in p['cases'] if c['generating_h']==1 and c['kind']=='positive']
    assert len(positives)==4
    for case in positives:
        q=b.request_for(case,1);truth=case['truth']
        verify(q,truth);verify(b.request_for(case,2),truth)
        assert all(len(codes)==1 for codes in truth['encoder']['codebook'].values())
        book=truth['encoder']['codebook'];seen={tuple(book[s][0]) for word in truth['plaintext']['words'] for s in word}
        held=case['holdout']['words']
        assert all(tuple(w[i:i+2]) in seen for w in held for i in range(0,len(w),2))
        assert case['generating_covered_holdout_words']==4


def test_existing_h2_results_reused_with_verified_witnesses(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare()
    cached=[c for c in p['cases'] if 'cached_h2_result' in c]
    assert len(cached)==11
    for case in cached:verify(b.request_for(case,2),case['cached_h2_result'])
