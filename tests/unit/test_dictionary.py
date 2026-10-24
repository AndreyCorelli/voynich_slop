import pytest

from voynich_smt.cipher.base import Bounds
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text


@pytest.mark.parametrize("words", [(), ("",), ("a", "a"), ("a b",)])
def test_invalid_dictionary(words):
    with pytest.raises(ValueError):
        WordDictionary.from_strings(words)


def test_candidates_use_public_length_bounds():
    vocabulary = WordDictionary.from_strings(("a", "ab", "abba"))
    assert vocabulary.candidates(3, Bounds("verbose", 1, 1, 3), 1, 4) == (tuple("a"), tuple("ab"))
    assert vocabulary.candidates(3, Bounds("verbose", 1, 1, 3), 2, 4) == (tuple("ab"),)
    assert vocabulary.accepts(Text.from_string("a ab"))
    assert not vocabulary.accepts(Text.from_string("ba"))
    with pytest.raises(ValueError):
        vocabulary.validate(Alphabet(("a",)))
