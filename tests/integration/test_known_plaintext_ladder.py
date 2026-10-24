from dataclasses import asdict
import json
from pathlib import Path

from benchmarks import known_plaintext_ladder as benchmark
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import Recovery


def test_known_plaintext_recovery_keeps_positions_and_prefix_free_roundtrip():
    plain=Text.from_string('ab aac');enc=Encoder({'a':(('x',),),'b':(('y','z'),),'c':(('w',),)})
    cipher=enc.encode(plain,(0,)*plain.size)
    q=HiddenRecoveryRequest(cipher,Alphabet(tuple('abc')),Alphabet(tuple('xyzw')),
        Bounds('verbose',2,1,3),WordDictionary(plain.words),timeout_ms=1000)
    result=asdict(benchmark.solve(plain,q))
    assert result['status']=='SAT' and tuple(map(tuple,result['plaintext']['words']))==plain.words
    verify(q,result)


def test_matched_ladder_scores_unchanged_continuation(tmp_path,monkeypatch):
    root=Path('experiments/results/predictive-calibration')
    m=json.loads((root/'prepared.json').read_text());hidden=json.loads((root/'size-ladder-10000ms.json').read_text())
    entry=next(e for e in m['cases'] if e['id']=='latin-synthetic')
    for key in ('public_input','truth_path','holdout'):entry[key]=str(Path(entry[key]).resolve())
    truth=json.loads(Path(entry['truth_path']).read_text());encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in truth['encoder']['codebook'].items()})
    hidden['manifest_sha256']=digest(m)
    (tmp_path/'prepared.json').write_text(json.dumps(m));(tmp_path/'size-ladder-10000ms.json').write_text(json.dumps(hidden))
    monkeypatch.setattr(benchmark,'ROOT',tmp_path)
    calls=[]
    def solve(plain,q):
        calls.append(plain)
        return Recovery('SAT',0,encoder=encoder,plaintext=plain,
                        choices=tuple(truth['choices'][:plain.size]),verified=True)
    monkeypatch.setattr(benchmark,'solve',solve)
    report=benchmark.run()
    assert [len(p.words) for p in calls]==[5,10,15]
    assert all(e['holdout_score']['dictionary_words']==e['exact_generating_plaintext_words']==22 for e in report['experiments'])
    assert all(e['hidden_result']=='UNKNOWN' for e in report['experiments'])
