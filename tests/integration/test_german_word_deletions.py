from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

import benchmarks.german_word_deletions as benchmark
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes
from voynich_smt.solver.recovery import Recovery


@pytest.mark.parametrize('vocabulary,status', [(('a', 'b', 'ab'), 'SAT'), (('a', 'b', 'aa'), 'UNSAT')])
def test_duplicate_equivalence_on_sat_and_shared_key_unsat(vocabulary, status):
    request = HiddenRecoveryRequest(Text.from_string('x y xy xy x'), Alphabet(tuple('ab')),
        Alphabet(tuple('xy')), Bounds('verbose', 1, 1, 1), WordDictionary.from_strings(vocabulary),
        timeout_ms=1000, dictionary_encoding='trie')
    unique, kept, removed = benchmark.deduplicate(request)
    assert kept == [0, 1, 2] and removed == [3, 4]
    for q in (request, unique):
        result = asdict(recover_observed_codes(q))
        assert result['status'] == status
        verify(q, result)
    with pytest.raises(ValueError, match='free'):
        benchmark.deduplicate(replace(request, selection=HomophoneSelection('cycle', 'text')))


def test_projection_retains_free_choices_and_handles_empty_span_metadata():
    plain = Text.from_string('ab aa ab b')
    encoder = Encoder({'a': (('x',), ('y',)), 'b': (('z',),)})
    choices = (0, 0, 1, 0, 1, 0, 0)
    cipher = encoder.encode(plain, choices)
    q = HiddenRecoveryRequest(cipher, Alphabet(tuple('ab')), Alphabet(tuple('xyz')),
        Bounds('verbose', 2, 1, 1), WordDictionary.from_strings(('ab', 'aa', 'b')))
    result = {'status': 'SAT', 'verified': True, 'encoder': asdict(encoder),
              'plaintext': asdict(plain), 'choices': choices, 'nulls': [], 'segmentation': [], 'code_spans': []}
    target, witness = benchmark.project_witness(q, result, [0, 2, 3])
    assert witness['choices'] == [0, 0, 1, 0, 0]
    assert target.ciphertext.words == (cipher.words[0], cipher.words[2], cipher.words[3])
    verify(target, witness)
    with pytest.raises(ValueError, match='ordered'):
        benchmark.project_witness(q, result, [2, 0])


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUTPUT', tmp_path/'checkpoint.json')
    monkeypatch.setattr(benchmark, 'ARTIFACTS', tmp_path/'inputs')


def test_real_duplicate_removal_and_endpoint_certificates(isolated):
    report = benchmark.run(1000, prepare_only=True)
    assert report['unique_words'] == 21
    assert report['duplicate_removals_original_positions'] == [16, 19, 24, 27]
    assert report['summary']['necessary_words_original_positions'] == [5, 29]
    base = HiddenRecoveryRequest.from_dict(report['base_request'])
    for entry in report['prepared_inputs']:
        payload = json.loads(Path(entry['public_input']).read_text())
        assert digest(payload) == entry['input_sha256']
        q = HiddenRecoveryRequest.from_dict(payload['request'])
        assert len(q.ciphertext.words) == 20
        assert replace(q, ciphertext=base.ciphertext, timeout_ms=base.timeout_ms) == base
    for row in report['experiments']:
        verify(HiddenRecoveryRequest.from_dict(row['request']), row['result'])


def test_unknown_then_larger_budget_retries_single_character(isolated, monkeypatch):
    calls = []
    def solve(request):
        calls.append(request.timeout_ms)
        return Recovery('UNKNOWN', 0)
    monkeypatch.setattr(benchmark, 'recover_observed_codes', solve)
    report = benchmark.run(1000)
    assert report['experiments'][-1]['deleted_original_position'] == 23
    assert 23 in report['summary']['unresolved_original_positions']
    assert not report['single_deletion_minimal']
    benchmark.run(2000, resume=True)
    assert calls == [1000, 2000]
    cached = json.loads(benchmark.OUTPUT.read_text())
    cached['experiments'][-1]['input_sha256'] = 'tampered'
    benchmark.OUTPUT.write_text(json.dumps(cached))
    with pytest.raises(ValueError, match='mismatch'):
        benchmark.run(2000, resume=True)
