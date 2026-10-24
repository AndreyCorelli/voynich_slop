from dataclasses import replace
import json
from pathlib import Path

from benchmarks import latin_mixed_comparison as benchmark
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.contractions import expand_units
from voynich_smt.models.settings import HomophoneSelection


def test_full_vocabulary_models_and_positive_truth(tmp_path,monkeypatch):
    monkeypatch.setattr(benchmark,'ARTIFACTS',tmp_path/'inputs')
    monkeypatch.setattr(benchmark,'RESULTS',tmp_path/'results')
    report=benchmark.prepare(1000)
    base=HiddenRecoveryRequest.from_dict(json.loads(benchmark.BASELINE.read_text())['request'])
    inventory=json.loads(benchmark.INVENTORY.read_text())
    source={''.join(w) for w in base.dictionary.words}
    assert len(report['prepared_inputs'])==6
    models={}
    for e in report['prepared_inputs']:
        payload=json.loads(Path(e['public_input']).read_text())
        assert set(payload)=={'request','codeword_domains'}
        assert digest(payload)==e['input_sha256']
        q=HiddenRecoveryRequest.from_dict(payload['request'])
        rules=[r for r in inventory['rules'] if r['id'] in inventory['profiles'][e['profile']]]
        assert {expand_units(w,rules) for w in q.dictionary.words}==source
        assert replace(q,ciphertext=base.ciphertext,dictionary=base.dictionary,
            plaintext_alphabet=base.plaintext_alphabet,timeout_ms=base.timeout_ms,
            selection=base.selection,max_word_length=base.max_word_length)==base
        assert q.selection==HomophoneSelection('free')
        if e['kind']=='voynich':
            assert q.ciphertext==base.ciphertext
            models[e['profile']]=set(q.dictionary.words)
        else:
            truth=json.loads(Path(e['truth_path']).read_text())
            assert digest(truth)==e['truth_sha256'];verify(q,truth)
            assert [expand_units(w,rules) for w in truth['plaintext']['words']]==e['expanded_plaintext']
    assert models['letters'] < models['ae-only'] < models['bounded-seven']
    assert {len(models[p]) for p in models}=={5655,5937,6804}


def test_voynich_probe_skips_unresolved_calibration(tmp_path,monkeypatch):
    from dataclasses import asdict
    from voynich_smt.data.corpus import write_json
    from voynich_smt.solver.recovery import Recovery
    monkeypatch.setattr(benchmark,'ARTIFACTS',tmp_path/'inputs')
    monkeypatch.setattr(benchmark,'RESULTS',tmp_path/'results')
    report=benchmark.prepare(1000);report['experiments']=[]
    for e in report['prepared_inputs']:
        if e['kind']!='positive':continue
        result=(json.loads(Path(e['truth_path']).read_text()) if e['profile']=='bounded-seven'
                else asdict(Recovery('UNKNOWN',0)))
        report['experiments'].append({**e,'result':result})
    write_json(tmp_path/'results'/'calibration-1000ms.json',report)
    calls=[]
    def solve(q):
        calls.append(q);return Recovery('UNKNOWN',0)
    monkeypatch.setattr(benchmark,'recover_observed_codes',solve)
    result=benchmark.voynich_probe(1000)
    assert len(calls)==1
    assert result['skipped_profiles']==['letters','ae-only']
    assert result['experiments'][0]['id']=='bounded-seven-voynich'
