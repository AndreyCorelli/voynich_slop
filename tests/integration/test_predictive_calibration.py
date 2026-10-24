import json
from pathlib import Path
import pytest
from benchmarks import predictive_calibration as benchmark
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.cipher.base import Encoder
from voynich_smt.models.text import Text


def test_selection_breaks_on_uncovered_words_and_does_not_cross_folio():
    rows=[{'tokens':list(w),'folio':f} for w,f in [('a','f1'),('z','f1'),('b','f1'),('c','f1')]]
    text,indices=benchmark.first_run(rows,size=2,dictionary={('a',),('b',),('c',)})
    assert indices==[2,3] and text==Text.from_string('b c')
    with pytest.raises(ValueError):benchmark.first_run(rows,size=5)
    rows[3]['folio']='f2'
    with pytest.raises(ValueError):benchmark.first_run(rows[2:],size=2,same_folio=True)


def test_six_case_protocol_and_hidden_truth(tmp_path,monkeypatch):
    monkeypatch.setattr(benchmark,'ROOT',tmp_path/'inputs')
    monkeypatch.setattr(benchmark,'OUT',tmp_path/'results')
    manifest=benchmark.prepare();assert len(manifest['cases'])==6
    inputs={}
    for entry in manifest['cases']:
        payload=json.loads(Path(entry['public_input']).read_text());assert digest(payload)==entry['input_sha256']
        assert set(payload)=={'request','codeword_domains'}
        q=HiddenRecoveryRequest.from_dict(payload['request']);assert len(q.ciphertext.words)==30 and q.selection.mode=='free'
        held=json.loads(Path(entry['holdout']).read_text());assert digest(held)==entry['holdout_sha256']
        assert len(held['ciphertext']['words'])==22
        inputs[entry['id']]=q
        if entry['kind']=='synthetic':
            truth=json.loads(Path(entry['truth_path']).read_text());assert digest(truth)==entry['truth_sha256']
            encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in truth['encoder']['codebook'].items()})
            plain=Text(tuple(map(tuple,truth['plaintext']['words'])))
            whole=encoder.encode(plain,tuple(truth['choices']))
            assert whole.words[:30]==q.ciphertext.words
            assert whole.words[30:]==tuple(map(tuple,held['ciphertext']['words']))
            assert entry['generating_holdout_score']['dictionary_words']==22
            assert set(plain.words)<=set(q.dictionary.words)
    assert inputs['latin-voynich'].ciphertext==inputs['swabian-voynich'].ciphertext
    assert inputs['latin-shuffle'].ciphertext==inputs['swabian-shuffle'].ciphertext


def test_unknown_is_not_prediction_failure(tmp_path,monkeypatch):
    from voynich_smt.solver.recovery import Recovery
    monkeypatch.setattr(benchmark,'ROOT',tmp_path/'inputs');monkeypatch.setattr(benchmark,'OUT',tmp_path/'results')
    monkeypatch.setattr(benchmark,'recover_observed_codes',lambda q:Recovery('UNKNOWN',0))
    result=benchmark.run_case('latin-synthetic',1000)
    assert result['evaluation_status']=='NOT_EVALUATED_NO_SAT'
    assert 'holdout_score' not in result and 'predictive_gate_passed' not in result
    with pytest.raises(ValueError,match='already exists'):benchmark.run_case('latin-synthetic',1000)
