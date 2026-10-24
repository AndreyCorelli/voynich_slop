import pytest

from voynich_smt.cipher.base import Bounds, Encoder, generate_ciphertext, generate_encoder
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import recover


@pytest.mark.parametrize("bounds,cipher", [
    (Bounds("monoalphabetic", 1, 1, 1), "xy"),
    (Bounds("homophonic", 2, 1, 1), "wxyz"),
    (Bounds("verbose", 2, 1, 3), "xyz"),
    (Bounds("verbose", 1, 3, 3), "xy"),
])
@pytest.mark.parametrize("source", ["a", "aaaa", "ab ab", "abba baab"])
@pytest.mark.parametrize("representation", ["ite", "array", "interval", "chunk", "finite"])
def test_seeded_round_trip(bounds, cipher, source, representation):
    plain, ca = Alphabet(tuple("ab")), Alphabet(tuple(cipher))
    text = Text.from_string(source)
    original = generate_encoder(plain, ca, bounds, 17)
    ciphertext, _ = generate_ciphertext(text, original, 19)
    result = recover(text, ciphertext, plain, ca, bounds, representation=representation)
    assert result.status == "SAT"
    assert result.verified
    assert result.encoder.encode(result.plaintext, result.choices) == ciphertext
    assert result.encoder.decode(ciphertext) == text
    for word, offsets in zip(ciphertext.words, result.segmentation):
        assert offsets[0] == 0 and offsets[-1] == len(word)


@pytest.mark.parametrize("plain,cipher,bounds", [
    ("aa", "xy", Bounds("monoalphabetic", 1, 1, 1)),
    ("ab", "xx", Bounds("homophonic", 2, 1, 1)),
    ("a", "xyz", Bounds("verbose", 1, 1, 2)),
    ("a b", "xy", Bounds("verbose", 1, 1, 2)),
    ("aaa", "xyz", Bounds("homophonic", 2, 1, 1)),
])
def test_impossible_cases(plain, cipher, bounds):
    result = recover(Text.from_string(plain), Text.from_string(cipher),
                     Alphabet(tuple("ab")), Alphabet(tuple("xyz")), bounds)
    assert result.status == "UNSAT"
    assert not result.verified


def test_prefix_collision_is_unsat():
    result = recover(Text.from_string("a b"), Text.from_string("x xy"),
                     Alphabet(tuple("ab")), Alphabet(tuple("xy")), Bounds("verbose", 1, 1, 2))
    assert result.status == "UNSAT"


def test_partially_symbolic_plaintext():
    result = recover(Text.from_string("ab aa"), Text.from_string("xy xx"),
                     Alphabet(tuple("ab")), Alphabet(tuple("xy")),
                     Bounds("homophonic", 1, 1, 1), domains={1: ("a", "b")})
    assert result.status == "SAT" and result.verified
    assert result.plaintext == Text.from_string("ab aa")


def test_multicharacter_atomic_glyphs():
    text = Text.from_string("aba")
    encoder = Encoder({"a": (("qo",),), "b": (("ch", "dy"),)})
    result = recover(text, encoder.encode(text, (0, 0, 0)), Alphabet(tuple("ab")),
                     Alphabet(("qo", "ch", "dy")), Bounds("verbose", 1, 1, 2))
    assert result.status == "SAT" and result.verified


def test_empty_text():
    result = recover(Text(()), Text(()), Alphabet(("a",)), Alphabet(("x",)),
                     Bounds("monoalphabetic", 1, 1, 1))
    assert result.status == "SAT" and result.verified


def test_invalid_input():
    with pytest.raises(ValueError):
        recover(Text.from_string("c"), Text.from_string("x"), Alphabet(tuple("ab")),
                Alphabet(("x",)), Bounds("monoalphabetic", 1, 1, 1))
