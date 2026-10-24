from dataclasses import replace
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

import benchmarks.german_regional_audit as benchmark
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


@pytest.mark.parametrize('raw,expected', [('[T]U', ['tu']), ('[D]As', ['das']),
    ('[F]Reilich', ['freilich']), ('a[?]r', None), ('v[?]', None), ('e*', None),
    ('[O]', None), ('hübsch', ['hübsch']), ('o', ['o'])])
def test_whole_word_mark_handling_does_not_create_letter_fragments(raw, expected):
    assert benchmark.normalized_v2(raw)[0] == expected


def test_corrected_counts_quarantine_whole_forms_and_retain_real_short_words():
    root = ET.fromstring('<root><wortform nr="1"><morph>[T]U</morph></wortform><wortform nr="2"><morph>a[?]r</morph></wortform><wortform nr="3"><morph>a</morph></wortform><wortform nr="4"><morph>h</morph></wortform><eingriff><wortform><morph>fake</morph></wortform></eingriff></root>')
    counts, events = benchmark.corrected_counts(root, {'h': 'letter mention'})
    assert dict(counts) == {'tu': 1, 'a': 1}
    assert [e['action'] for e in events] == ['joined_marked_initial', 'quarantined_uncertain_or_marked', 'excluded_nonlexical_or_unresolved']


def test_real_three_source_audits_preserve_cipher_and_original_alphabets(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'ARTIFACTS', tmp_path/'inputs')
    monkeypatch.setattr(benchmark, 'RESULTS', tmp_path/'results')
    report = benchmark.run(1000)
    assert report['experiments'] == [] and not report['complete']
    expected = {123: (3181, ['a', 'o'], ['t', 'u']),
                153: (2616, ['a', 'o'], ['h', 'u']),
                233: (3133, ['e', 'o'], ['d', 'r'])}
    full = HiddenRecoveryRequest.from_dict(json.loads(benchmark.FULL.read_text())['request'])
    old = json.loads(benchmark.ROBUSTNESS.read_text())
    for row in report['rows']:
        n = row['source_id'];size, one, missing = expected[n]
        assert row['corrected_vocabulary_size'] == size
        assert row['remaining_one_letter_words'] == one
        assert row['witness_words_missing_after_correction'] == missing
        payload = json.loads(Path(row['public_input']).read_text())
        assert digest(payload) == row['input_sha256']
        assert set(payload) == {'request', 'codeword_domains'}
        request = HiddenRecoveryRequest.from_dict(payload['request'])
        assert request.ciphertext == full.ciphertext
        assert replace(request, dictionary=full.dictionary, plaintext_alphabet=full.plaintext_alphabet,
                       timeout_ms=full.timeout_ms) == full
        entry = next(e for e in old['experiments'] if e['source_id'] == n)
        original = HiddenRecoveryRequest.from_dict(json.loads(Path(entry['public_input']).read_text())['request'])
        assert request.plaintext_alphabet == original.plaintext_alphabet
        vocabulary = json.loads(Path(row['vocabulary_path']).read_text())
        assert digest(vocabulary) == row['vocabulary_sha256']
        assert [''.join(w) for w in request.dictionary.words] == vocabulary['words']
    benchmark.run(1000, resume=True)
