from dataclasses import asdict
import json
import pytest
from benchmarks import synthetic_prefix as runner
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.cipher.selection import choose
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import Recovery


def fixture(tmp_path):
    plain = Text.from_string('aba b ab')
    encoder = Encoder({'a': (tuple('xxx'), ('z',)), 'b': (('y',),)})
    selection = HomophoneSelection('cycle', 'text')
    choices = choose(plain, encoder, selection)
    request = HiddenRecoveryRequest(encoder.encode(plain, choices), Alphabet(tuple('ab')),
        Alphabet(tuple('xyz')), Bounds('verbose', 2, 1, 3),
        WordDictionary.from_strings(('aba','b','ab')), selection=selection, dictionary_encoding='trie')
    payload = {'request': asdict(request), 'cycle_encoding': 'state'}
    public_path, truth_path, source_path = [tmp_path / n for n in ('input.json','truth.json','source.json')]
    write_json(public_path, payload)
    write_json(truth_path, {'plaintext':asdict(plain),'encoder':asdict(encoder),'choices':choices,'nulls':[]})
    write_json(source_path, {'complete':True,'experiments':[{'seed':7,'cycle_encoding':'state',
        'vocabulary_size':3,'public_input':str(public_path),'input_sha256':digest(payload),'truth':str(truth_path)}]})
    return request, {'source_report':str(source_path),'seed':7,'word_counts':[1,2,3],'timeout_ms':1000}


def test_prefixes_preserve_vocabulary_and_truth_stays_out_of_solver(tmp_path, monkeypatch):
    request, config = fixture(tmp_path)
    calls = []
    def timeout(public, mode):
        calls.append(public)
        assert isinstance(public, HiddenRecoveryRequest) and mode == 'state'
        assert public.dictionary == request.dictionary and public.bounds == request.bounds
        assert public.selection == request.selection
        return Recovery('UNKNOWN', 0, 'test timeout')
    monkeypatch.setattr(runner, 'solve', timeout)
    output = tmp_path / 'report.json'
    result = runner.run(config, output, tmp_path / 'artifacts')
    assert [q.ciphertext.words for q in calls] == [request.ciphertext.words[:n] for n in (1,2,3)]
    assert result['complete'] and result['summary']['unknown_word_counts'] == [1,2,3]
    first_truth = json.loads((tmp_path/'artifacts/truth/seed-7-words-01.json').read_text())
    assert len(first_truth['choices']) == 3 and len(first_truth['plaintext']['words']) == 1
    assert digest(runner.run(config, output, tmp_path/'artifacts', resume=True)) == digest(result)
    assert len(calls) == 3
    path = tmp_path/'artifacts/inputs/seed-7-words-01.json'
    saved=json.loads(path.read_text()); saved['request']['timeout_ms']=1;write_json(path,saved)
    with pytest.raises(ValueError, match='changed'):
        runner.run(config, output, tmp_path/'artifacts',resume=True)


def test_positive_prefixes_recover_verified_fits(tmp_path):
    _, config = fixture(tmp_path)
    report = runner.run(config, tmp_path/'report.json',tmp_path/'artifacts')
    assert all(r['result']['verified'] for r in report['experiments'])
    assert report['summary']['verified_sat_word_counts'] == [1,2,3]
    assert report['summary']['first_sampled_unknown'] is None


def test_unsat_positive_control_is_recorded_then_rejected(tmp_path, monkeypatch):
    _,config=fixture(tmp_path)
    monkeypatch.setattr(runner,'solve',lambda *a:Recovery('UNSAT',0))
    output=tmp_path/'report.json'
    with pytest.raises(RuntimeError,match='positive control'):
        runner.run(config,output,tmp_path/'artifacts')
    assert json.loads(output.read_text())['experiments'][0]['result']['status']=='UNSAT'
    assert not json.loads(output.read_text())['complete']


def test_no_monotonicity_assumption_in_summary():
    rows=[{'word_count':n,'result':{'status':status}} for n,status in ((1,'SAT'),(2,'UNKNOWN'),(4,'SAT'))]
    assert runner.summarize(rows)['verified_sat_word_counts']==[1,4]
    assert runner.summarize(rows)['first_sampled_unknown']==2
