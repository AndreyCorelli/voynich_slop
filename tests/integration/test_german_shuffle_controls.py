from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

import benchmarks.german_shuffle_controls as benchmark
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import Recovery


@pytest.mark.parametrize('seed', [7, 17, 1729])
def test_typewise_shuffle_preserves_repeats_and_does_not_merge_anagram_types(seed):
    text = Text.from_string('ab ba ab c d c')
    shuffled, metadata = benchmark.typewise_shuffle(text, seed)
    assert shuffled != text
    assert shuffled == benchmark.typewise_shuffle(text, seed)[0]
    assert benchmark.repetition_partition(shuffled) == benchmark.repetition_partition(text)
    assert tuple(map(len, shuffled.words)) == tuple(map(len, text.words))
    assert all(Counter(a) == Counter(b) for a,b in zip(text.words, shuffled.words))
    assert len(set(shuffled.words)) == len(set(text.words))


def test_resampled_positive_matches_lengths_and_has_independently_valid_truth():
    plain = Text.from_string('ab aab ab')
    encoder = Encoder({'a': (('x',), ('y',)), 'b': (('z',), ('w',))})
    choices = (0,)*plain.size
    cipher = encoder.encode(plain, choices)
    request = HiddenRecoveryRequest(cipher, Alphabet(tuple('ab')), Alphabet(tuple('xyzw')),
        Bounds('verbose', 2, 1, 3), WordDictionary.from_strings(('ab', 'aab')))
    result = {'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':choices,'nulls':[]}
    q, truth = benchmark.positive_control(request, result, 7)
    assert replace(q, ciphertext=request.ciphertext) == request
    assert q.ciphertext != request.ciphertext
    assert tuple(map(len,q.ciphertext.words)) == tuple(map(len,request.ciphertext.words))
    assert truth['plaintext'] == asdict(plain)
    verify(q,truth)


@pytest.fixture(scope='module')
def prepared(tmp_path_factory):
    original = benchmark.ARTIFACTS
    benchmark.ARTIFACTS = tmp_path_factory.mktemp('shuffle-inputs')
    try:return benchmark.prepare(1000)
    finally:benchmark.ARTIFACTS = original


def test_real_paired_shuffles_and_positive_controls_have_fixed_models(prepared):
    baseline = json.loads(benchmark.BASELINE.read_text())
    originals = {}
    for n in benchmark.SOURCES:
        row = next(r for r in baseline['rows'] if r['source_id']==n)
        originals[n] = HiddenRecoveryRequest.from_dict(json.loads(Path(row['public_input']).read_text())['request'])
    assert len(prepared['prepared_inputs']) == 16
    for entry in prepared['prepared_inputs']:
        payload = json.loads(Path(entry['public_input']).read_text())
        assert digest(payload) == entry['input_sha256']
        assert set(payload) == {'request','codeword_domains'}
        q = HiddenRecoveryRequest.from_dict(payload['request']);base = originals[entry['source_id']]
        assert replace(q,ciphertext=base.ciphertext,timeout_ms=base.timeout_ms) == base
        assert tuple(map(len,q.ciphertext.words)) == tuple(map(len,base.ciphertext.words))
        if entry['kind']=='shuffle':
            assert Counter(g for w in q.ciphertext.words for g in w) == Counter(g for w in base.ciphertext.words for g in w)
            paired = next(e for e in prepared['prepared_inputs'] if e['kind']=='shuffle' and e['source_id']!=entry['source_id'] and e['family']==entry['family'] and e['seed']==entry['seed'])
            assert paired['ciphertext_sha256'] == entry['ciphertext_sha256']
            if entry['family']=='typewise':assert benchmark.repetition_partition(q.ciphertext) == benchmark.repetition_partition(base.ciphertext)
        else:
            truth = json.loads(Path(entry['truth_path']).read_text())
            assert digest(truth) == entry['truth_sha256']
            assert truth['generator']['changed_from_source']
            verify(q,truth)


def test_checkpoint_skips_finished_unknown_rows_and_rejects_tampering(prepared,tmp_path,monkeypatch):
    monkeypatch.setattr(benchmark,'prepare',lambda budget:deepcopy(prepared))
    monkeypatch.setattr(benchmark,'RESULTS',tmp_path)
    calls = []
    def solve(q):
        calls.append(q)
        return Recovery('UNKNOWN',0)
    monkeypatch.setattr(benchmark,'recover_observed_codes',solve)
    report = benchmark.run(1000,solve=True,max_solves=1)
    assert len(calls)==1 and not report['complete']
    benchmark.run(1000,solve=True,resume=True,max_solves=1)
    assert len(calls)==2
    path=tmp_path/'budget-1000ms.json';cached=json.loads(path.read_text());cached['experiments'][0]['input_sha256']='tampered';path.write_text(json.dumps(cached))
    with pytest.raises(ValueError,match='mismatch'):
        benchmark.run(1000,resume=True)
