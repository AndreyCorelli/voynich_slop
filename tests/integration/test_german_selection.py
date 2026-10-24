from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from benchmarks.german_selection import normalize_form, variants
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes


@pytest.mark.parametrize('raw,expected', [
    ('VND', ['vnd']), ('ſtraße', ['strasse']), ('hübsch', ['hübsch']),
    ('hu\u0364bsch', ['hübsch']), ('gu\u0366t', ['guot']),
    ('wër', ['wer']), ('leẅten', ['lewten']), ('dÿ', ['dy']),
    ('d`', ['der']), ("christ'", ['christus']),
    ('a\u0305', None), ('12', None), ('α', None),
])
def test_historical_spelling_and_uncertain_forms(raw, expected):
    assert normalize_form(raw) == expected


def test_german_variants_change_only_vocabulary_alphabet_budget_and_selection():
    base = HiddenRecoveryRequest.from_dict(json.loads(Path('experiments/results/conflict-selection.json').read_text())['baseline_request'])
    vocabulary = {'words': ['g', 'ä', 'gä'], 'alphabet': ['g', 'ä']}
    versions = variants(base, vocabulary, 1000)
    for name, version in versions.items():
        assert version.ciphertext == base.ciphertext
        assert version.dictionary == WordDictionary.from_strings(tuple(vocabulary['words']))
        assert version.plaintext_alphabet == Alphabet(('g', 'ä'))
        assert replace(version, dictionary=base.dictionary,
                       plaintext_alphabet=base.plaintext_alphabet,
                       timeout_ms=base.timeout_ms, selection=base.selection) == base
    assert replace(versions['free'], selection=versions['text-cycle'].selection) == versions['text-cycle']
    with pytest.raises(ValueError, match='baseline'):
        variants(replace(base, bounds=Bounds('verbose', 2, 1, 2)), vocabulary, 1000)


@pytest.mark.parametrize('policy', [HomophoneSelection(), HomophoneSelection('cycle', 'text')])
def test_umlaut_synthetic_control_is_verified_sat_under_both_policies(policy):
    plain = Text.from_string('gäg ägg')
    encoder = Encoder({'g': (('x',), ('y',)), 'ä': (('z',), ('w',))})
    cipher = encoder.encode(plain, (0, 0, 1, 1, 0, 1))
    request = HiddenRecoveryRequest(cipher, Alphabet(('g', 'ä')), Alphabet(tuple('xyzw')),
        Bounds('verbose', 2, 1, 3), WordDictionary.from_strings(('gäg', 'ägg')),
        timeout_ms=5000, selection=policy, dictionary_encoding='trie')
    result = asdict(recover_observed_codes(request))
    assert result['status'] == 'SAT'
    verify(request, result)
