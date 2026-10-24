from dataclasses import replace
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

import benchmarks.german_short_form_audit as benchmark
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def test_provenance_traversal_retains_real_morphs_and_excludes_editorial_material():
    root = ET.fromstring('<root><zeile nr="1"><wortform nr="a"><annotation><morph>fake</morph></annotation><morph>ab</morph> <morph>get</morph></wortform><name><wortform nr="b"><morph>Maria</morph></wortform></name><eingriff><wortform><morph>fake</morph></wortform></eingriff></zeile></root>')
    found = benchmark.occurrences(root)
    assert set(found) == {'ab', 'get', 'maria'}
    assert found['ab'][0]['parent_morph_forms'] == ['ab', 'get']
    assert 'Maria' in found['ab'][0]['line_words']
    assert found['ab'][0]['word_number'] == 'a'


def test_real_audit_and_dictionary_only_sensitivity(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path/'audit.json')
    monkeypatch.setattr(benchmark, 'INPUT', tmp_path/'input.json')
    report = benchmark.run()
    words = {e['word']: e for e in report['audit']}
    assert words['k']['source_occurrence_count'] == 4
    assert words['x']['source_occurrence_count'] == 2
    assert words['o']['source_occurrence_count'] == 5
    assert words['k']['witness_positions'] == [7, 23]
    for form in ('k', 'x'):
        for occurrence in words[form]['occurrences']:
            context = occurrence['line_words']
            assert any(context[i:i+3] == ['k', 'x', 'k'] for i in range(len(context)-2))
    original = HiddenRecoveryRequest.from_dict(json.loads(benchmark.RESULT.read_text())['request'])
    payload = json.loads(benchmark.INPUT.read_text())
    request = HiddenRecoveryRequest.from_dict(payload['request'])
    assert digest(payload) == report['sensitivity_input_sha256']
    assert set(payload) == {'request', 'codeword_domains'}
    assert replace(request, dictionary=original.dictionary, timeout_ms=original.timeout_ms) == original
    assert set(original.dictionary.words)-set(request.dictionary.words) == {('k',), ('x',)}
    assert set(request.dictionary.words)-set(original.dictionary.words) == set()
    assert request.dictionary.words and ('o',) in request.dictionary.words
    assert report['current_witness_rejected_by_filtered_dictionary']
    assert report['filtered_vocabulary_size'] == 2423
    assert report['solver_calls'] == 0
