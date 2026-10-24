from dataclasses import asdict

from benchmarks import full_vocabulary_h1 as b
from benchmarks.l3_conflict import verify
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.recovery import Recovery


def test_dictionary_is_only_matched_request_difference(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare()
    reduced=dict(p['requests']['reduced']);full=dict(p['requests']['full'])
    reduced.pop('dictionary');full.pop('dictionary')
    assert b.digest(reduced)==b.digest(full)
    assert p['protocol']['dictionary_sizes']=={'reduced':12,'full':5655}
    assert b.digest(b.prepare())==b.digest(p)


def test_full_alphabet_positive_novelty_and_coverage(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare()
    q=HiddenRecoveryRequest.from_dict(p['requests']['full']);verify(q,p['truth'])
    assert set(p['truth']['encoder']['codebook'])==set(q.plaintext_alphabet.symbols)
    assert not set(tuple(w) for w in p['truth']['plaintext']['words'])&set(tuple(w) for w in p['holdout_plaintext']['words'])
    assert not set(q.ciphertext.words)&set(tuple(w) for w in p['holdout']['words'])
    seen={tuple(m['code']) for m in b.used_mappings(p['truth'])}
    assert all(tuple(w[i:i+2]) in seen for w in p['holdout']['words'] for i in range(0,len(w),2))
    assert p['generating_score_full_dictionary']['novel_dictionary_words']==3


def test_unknown_is_unscored_and_finished_fits_are_not_repeated(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);calls=[]
    def unknown(*args,**kwargs):
        calls.append(1);return Recovery('UNKNOWN',0.01,reason_unknown='forced test timeout')
    monkeypatch.setattr(b,'_recover',unknown)
    r=b.run();assert len(calls)==2 and r['complete']
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in a for a in r['arms'])
    b.run();assert len(calls)==2
