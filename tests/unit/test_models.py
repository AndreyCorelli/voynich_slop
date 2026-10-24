import pytest

from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.cipher.base import Bounds, Encoder, generate_encoder


@pytest.mark.parametrize("symbols", [(), ("a", "a"), (" ",), ("",)])
def test_invalid_alphabet(symbols):
    with pytest.raises(ValueError):
        Alphabet(symbols)


def test_atomic_multicharacter_glyphs_and_boundaries():
    plain = Text((("a", "b"), ("a",)))
    encoder = Encoder({"a": (("ch",),), "b": (("qo", "dy"),)})
    ciphertext = encoder.encode(plain, (0, 0, 0))
    ciphertext.validate(Alphabet(("ch", "qo", "dy")))
    assert ciphertext.words == (("ch", "qo", "dy"), ("ch",))
    assert encoder.decode(ciphertext) == plain


@pytest.mark.parametrize("book", [
    {"a": (("x",),), "b": (("x", "y"),)},
    {"a": (("x",),), "b": (("x",),)},
    {"a": ((),)}, {"a": ()},
])
def test_nonreversible_codebook_rejected(book):
    with pytest.raises(ValueError):
        Encoder(book)


def test_generator_capacity_and_determinism():
    p, c = Alphabet(tuple("ab")), Alphabet(tuple("xy"))
    bounds = Bounds(max_homophones=2, max_code_length=3)
    assert generate_encoder(p, c, bounds, 9) == generate_encoder(p, c, bounds, 9)
    with pytest.raises(ValueError):
        generate_encoder(p, c, Bounds("homophonic", 2, 1, 1), 9)


def test_invalid_choice_and_partial_code():
    encoder = Encoder({"a": (("x", "y"),)})
    with pytest.raises(ValueError):
        encoder.encode(Text.from_string("a"), (-1,))
    with pytest.raises(ValueError):
        encoder.decode(Text.from_string("x"))
