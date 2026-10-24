import json
from pathlib import Path
import pytest

from benchmarks import synthetic_size_ladder as benchmark
from voynich_smt.cipher.base import Encoder
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import Recovery


def fixture_manifest(tmp_path,monkeypatch):
    original=json.loads(Path('experiments/results/predictive-calibration/prepared.json').read_text())
    entry=next(e for e in original['cases'] if e['id']=='latin-synthetic')
    for key in ('public_input','truth_path','holdout'):entry[key]=str(Path(entry[key]).resolve())
    base=json.loads(Path(entry['public_input']).read_text())['request']
    truth=json.loads(Path(entry['truth_path']).read_text())
    root=tmp_path/'experiments/results/predictive-calibration';root.mkdir(parents=True)
    (root/'prepared.json').write_text(json.dumps(original))
    monkeypatch.chdir(tmp_path)
    return base,truth


def test_fixed_prefixes_full_model_unknown_and_repeat_protection(tmp_path,monkeypatch):
    base,_=fixture_manifest(tmp_path,monkeypatch);calls=[]
    def solve(q):
        calls.append(q);return Recovery('UNKNOWN',0)
    monkeypatch.setattr(benchmark,'recover_observed_codes',solve)
    report=benchmark.run()
    assert [len(q.ciphertext.words) for q in calls]==[5,10,15]
    for q in calls:
        assert q.ciphertext.words==tuple(map(tuple,base['ciphertext']['words'][:len(q.ciphertext.words)]))
        assert q.dictionary.words==tuple(map(tuple,base['dictionary']['words']))
        assert q.plaintext_alphabet.symbols==tuple(base['plaintext_alphabet']['symbols'])
        assert q.timeout_ms==10000
    assert all('holdout_score' not in r for r in report['experiments'])
    with pytest.raises(ValueError,match='already recorded'):benchmark.run()


def test_sat_key_is_frozen_and_scores_original_continuation(tmp_path,monkeypatch):
    _,truth=fixture_manifest(tmp_path,monkeypatch)
    encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in truth['encoder']['codebook'].items()})
    def solve(q):
        plain=Text(tuple(map(tuple,truth['plaintext']['words'][:len(q.ciphertext.words)])))
        return Recovery('SAT',0,encoder=encoder,plaintext=plain,
                        choices=tuple(truth['choices'][:plain.size]),verified=True)
    monkeypatch.setattr(benchmark,'recover_observed_codes',solve)
    report=benchmark.run()
    assert all(r['holdout_score']['word_count']==r['holdout_score']['dictionary_words']==22 for r in report['experiments'])
