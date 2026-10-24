import json
from pathlib import Path
import pytest

from benchmarks import reduced_vocabulary_calibration as benchmark
from voynich_smt.solver.recovery import Recovery


def test_nested_seeded_distractors_preserve_required_words_and_reject_bad_sizes():
    full=tuple((str(i),) for i in range(100));required=full[:10]
    result=benchmark.nested_vocabularies(full,required,[16,32,64],1729)
    assert set(required)<=set(result[16].words)<set(result[32].words)<set(result[64].words)
    assert [len(v.words) for v in result.values()]==[16,32,64]
    assert result==benchmark.nested_vocabularies(full,required,[16,32,64],1729)
    with pytest.raises(ValueError):benchmark.nested_vocabularies(full,required,[5],1729)
    with pytest.raises(ValueError):benchmark.nested_vocabularies(full,required,[32,16],1729)


def test_generating_codeword_coverage_tracks_homophones_not_only_letters():
    truth={'encoder':{'codebook':{'a':[['x'],['y']]}},
           'plaintext':{'words':[['a']]*52},'choices':[0]*30+[0,1]*11}
    assert sum(benchmark.codeword_coverage(truth,5))==11
    truth['choices'][1]=1
    assert all(benchmark.codeword_coverage(truth,5))


def test_matrix_uses_fixed_prefixes_alphabets_and_resume_skips_unknown(tmp_path,monkeypatch):
    manifest=json.loads(Path('experiments/results/predictive-calibration/prepared.json').read_text())
    entry=next(e for e in manifest['cases'] if e['id']=='latin-synthetic')
    for k in ('public_input','truth_path','holdout'):entry[k]=str(Path(entry[k]).resolve())
    original=json.loads(Path(entry['public_input']).read_text())['request']
    (tmp_path/'prepared.json').write_text(json.dumps(manifest));monkeypatch.setattr(benchmark,'ROOT',tmp_path)
    calls=[]
    def recover(q):calls.append(q);return Recovery('UNKNOWN',0)
    monkeypatch.setattr(benchmark,'recover_observed_codes',recover)
    report=benchmark.run();assert len(calls)==9 and report['complete']
    assert [len(q.ciphertext.words) for q in calls]==[5]*3+[10]*3+[15]*3
    assert [len(q.dictionary.words) for q in calls]==[64,128,256]*3
    for q in calls:
        assert q.plaintext_alphabet.symbols==tuple(original['plaintext_alphabet']['symbols'])
        assert q.ciphertext.words==tuple(map(tuple,original['ciphertext']['words'][:len(q.ciphertext.words)]))
    assert all(e['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'holdout_score_full_dictionary' not in e for e in report['experiments'])
    benchmark.run(resume=True);assert len(calls)==9
    cached=json.loads((tmp_path/'reduced-vocabulary-10000ms.json').read_text());cached['experiments'][0]['request_sha256']='changed'
    (tmp_path/'reduced-vocabulary-10000ms.json').write_text(json.dumps(cached))
    with pytest.raises(ValueError,match='mismatch'):benchmark.run(resume=True)
