from dataclasses import asdict
from benchmarks import flat_trie_comparison as b
from voynich_smt.data.corpus import digest
from voynich_smt.solver.recovery import Recovery


def test_only_encoding_changes(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    source,p=b.prepare()
    for case in p['cases']:
        flat=dict(case['requests']['flat']);trie=dict(case['requests']['trie'])
        assert flat.pop('dictionary_encoding')=='flat' and trie.pop('dictionary_encoding')=='trie'
        assert flat==trie and flat['timeout_ms']==5000
        assert not any(k in case for k in ('truth','revealed_lengths','holdout'))


def test_two_new_trie_fits_flat_reuse_unknown_unscored(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def spy(q):
        received.append(q)
        return Recovery('UNKNOWN',0.01,reason_unknown='forced',capacity={'construction_seconds':0})
    monkeypatch.setattr(b,'recover_observed_codes',spy)
    r=b.run();source,p=b.prepare()
    assert len(received)==2 and all(q.dictionary_encoding=='trie' and q.timeout_ms==5000 for q in received)
    assert sum(a['reused'] for a in r['arms'])==2
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in a for a in r['arms'])
    assert [digest(asdict(q)) for q in received]==[digest(c['requests']['trie']) for c in p['cases']]
    assert digest(b.run())==digest(r) and len(received)==2
    b.validate()
