from dataclasses import asdict
import xml.etree.ElementTree as ET

import pytest

from benchmarks.german_passages import extract_records, scan, solve_known, verify_known, repetition_conflicts
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text


def records(words):
    return [{'word': w, 'morph_index': i, 'part': 0} for i, w in enumerate(words)]


def test_extraction_preserves_order_umlauts_and_gaps_without_joining_morphs():
    root = ET.fromstring('''<root><bibliographie><wortform><morph>omit</morph></wortform></bibliographie>
    <absatz><wortform><morph>VND</morph><morph>hübsch</morph></wortform></absatz>
    <eingriff>insert</eingriff><wortform><morph>a̅</morph></wortform>
    <ueberschrift>heading</ueberschrift><absatz><wortform><morph>wer</morph></wortform></absatz></root>''')
    extracted = extract_records(root)
    assert [r['word'] for r in extracted] == ['vnd', 'hübsch', None, None, None, 'wer']
    assert [r['morph_index'] for r in extracted if r['word']] == [0, 1, 3]


def test_windows_never_bridge_unknown_or_editorial_gaps():
    stats, candidates = scan(records(['a', None, 'b']), [1, 1], Bounds('verbose', 2, 1, 3))
    assert stats['windows'] == 0 and not candidates
    stats, candidates = scan(records(['a', 'b', None, 'c', 'd']), [1, 1], Bounds('verbose', 2, 1, 3))
    assert stats['windows'] == 2
    assert [e['plaintext'] for e in candidates] == [['a', 'b'], ['c', 'd']]


def test_total_length_match_is_insufficient_and_positionwise_filter_is_inclusive():
    stats, candidates = scan(records(['aaaa', 'b']), [2, 3], Bounds('verbose', 2, 1, 3))
    assert stats['total_length_compatible'] == 1
    assert stats['positionwise_length_compatible'] == 0
    assert stats['incompatible_windows_by_position'] == [1, 0]
    stats, candidates = scan(records(['aa', 'b']), [2, 3], Bounds('verbose', 2, 1, 3))
    assert stats['positionwise_length_compatible'] == 1
    assert candidates[0]['start_record'] == 0 and candidates[0]['end_record_exclusive'] == 2
    stats, candidates = scan(records(['a', 'b']), [4, 1], Bounds('verbose', 2, 1, 3))
    assert not candidates  # Too few plaintext letters to emit four characters.


def test_explicit_section_marker_breaks_passages_without_becoming_a_word():
    root = ET.fromstring('<root><wortform><morph>a</morph><morph>§</morph><morph>b</morph></wortform></root>')
    extracted = extract_records(root)
    assert [r['word'] for r in extracted] == ['a', None, 'b']
    stats, candidates = scan(extracted, [1, 1], Bounds())
    assert stats['windows'] == 0 and not candidates


def known_request(plain, cipher):
    return HiddenRecoveryRequest(cipher, Alphabet(('g', 'ä')), Alphabet(tuple('xyzw')),
        Bounds('verbose', 2, 1, 3), WordDictionary.from_strings(tuple(sorted(set(''.join(w) for w in plain.words)))),
        timeout_ms=5000, selection=HomophoneSelection('cycle', 'text'), dictionary_encoding='trie')


def test_known_cyclic_umlaut_control_has_a_verified_sat_key():
    plain = Text.from_string('gäg ägg')
    encoder = Encoder({'g': (('x',), ('y',)), 'ä': (('z',), ('w',))})
    cipher = encoder.encode(plain, (0, 0, 1, 1, 0, 1))
    request = known_request(plain, cipher)
    result = solve_known(request, plain)
    assert result['status'] == 'SAT' and result['verified']
    verify_known(request, plain, result)
    wrong = Text.from_string('ägg gäg')
    assert request.dictionary.accepts(wrong)
    with pytest.raises(ValueError, match='different passage'):
        verify_known(request, wrong, result)


def test_attested_order_is_not_relaxed_to_dictionary_membership():
    plain = Text.from_string('gä äg')
    # Equal ciphertext words must decode equally; these attested words differ.
    request = known_request(plain, Text.from_string('xy xy'))
    result = solve_known(request, plain)
    assert result['status'] == 'UNSAT'


def test_empty_ciphertext_is_rejected():
    with pytest.raises(ValueError, match='Nonempty'):
        scan(records(['a']), [], Bounds())


def test_equal_ciphertext_words_require_equal_plaintext_but_not_the_converse():
    conflicts = repetition_conflicts(Text.from_string('xy xy zz'), ['ab', 'ba', 'ab'])
    assert conflicts == [{'left_word': 0, 'right_word': 1, 'ciphertext_word': 'xy',
                          'left_plaintext': 'ab', 'right_plaintext': 'ba'}]
    assert repetition_conflicts(Text.from_string('xy zz'), ['ab', 'ab']) == []
    with pytest.raises(ValueError, match='Word counts'):
        repetition_conflicts(Text.from_string('xy xy'), ['ab'])
