from dataclasses import replace
import pytest
from benchmarks.conflict_selection import selection_variants
from voynich_smt.cipher.base import Bounds
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text


def baseline():
    return HiddenRecoveryRequest(Text.from_string('xy z'),Alphabet(tuple('ab')),
        Alphabet(tuple('xyz')),Bounds('verbose',2,1,3),WordDictionary.from_strings(('a','b','ab')),
        selection=HomophoneSelection('cycle','text'),dictionary_encoding='trie')


@pytest.mark.parametrize('name,policy',[('free',HomophoneSelection()),
    ('word-reset',HomophoneSelection('cycle','word'))])
def test_selection_comparison_preserves_all_other_scientific_parameters(name,policy):
    base=baseline();variant=selection_variants(base,30000)[name]
    assert variant.selection==policy and variant.timeout_ms==30000
    assert replace(variant,selection=base.selection,timeout_ms=base.timeout_ms)==base


def test_selection_comparison_requires_text_wide_cyclic_baseline():
    with pytest.raises(ValueError,match='baseline'):
        selection_variants(replace(baseline(),selection=HomophoneSelection()),30000)
