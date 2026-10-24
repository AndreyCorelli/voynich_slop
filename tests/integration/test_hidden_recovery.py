from itertools import product

import pytest
import z3

from voynich_smt.cipher.base import Bounds, Encoder, generate_ciphertext, generate_encoder
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import recover_dictionary


@pytest.mark.parametrize("seed", [7, 17, 1729])
@pytest.mark.parametrize("representation", ["ite", "array", "interval", "chunk", "finite"])
@pytest.mark.parametrize("bounds", [Bounds("monoalphabetic", 1, 1, 1),
                                      Bounds("homophonic", 2, 1, 1),
                                      Bounds("verbose", 2, 1, 3)])
def test_hidden_plaintext_key_segmentation_and_choices(seed, bounds, representation):
    vocabulary = WordDictionary.from_strings(("amo", "amor", "ora", "oro", "mora"))
    pa, ca = Alphabet(tuple("amor")), Alphabet(tuple("abcdefgh"))
    truth = Text.from_string("amo amor ora oro mora")
    encoder = generate_encoder(pa, ca, bounds, seed)
    ciphertext, _ = generate_ciphertext(truth, encoder, seed + 1)
    # No truth, original key, word lengths, offsets, or choices cross this API.
    result = recover_dictionary(ciphertext, pa, ca, bounds, vocabulary,
                                representation=representation)
    assert result.status == "SAT" and result.verified
    assert vocabulary.accepts(result.plaintext)
    assert result.encoder.encode(result.plaintext, result.choices) == ciphertext
    assert result.encoder.decode(ciphertext) == result.plaintext
    assert len(result.choices) == result.plaintext.size
    assert [len(offsets) - 1 for offsets in result.segmentation] == list(map(len, result.plaintext.words))


def test_plaintext_word_lengths_are_hidden():
    # Both one- and two-token words pass public ciphertext-length pruning.
    vocabulary = WordDictionary.from_strings(("a", "bb"))
    result = recover_dictionary(Text.from_string("xy xy"), Alphabet(tuple("ab")),
                                Alphabet(tuple("xyz")), Bounds("verbose", 1, 1, 2), vocabulary)
    assert result.status == "SAT" and result.verified
    assert result.plaintext == Text.from_string("a a")
    assert result.segmentation == ((0, 2), (0, 2))


@pytest.mark.parametrize("cipher,vocabulary,bounds", [
    ("xx", ("ab",), Bounds("monoalphabetic", 1, 1, 1)),
    ("x", ("ab",), Bounds("verbose", 1, 1, 3)),
    ("xyz", ("ab",), Bounds("monoalphabetic", 1, 1, 1)),
])
def test_dictionary_incompatibility_is_unsat(cipher, vocabulary, bounds):
    result = recover_dictionary(Text.from_string(cipher), Alphabet(tuple("ab")),
                                Alphabet(tuple("xyz")), bounds, WordDictionary.from_strings(vocabulary))
    assert result.status == "UNSAT" and not result.verified


def test_public_word_length_bounds_are_enforced():
    result = recover_dictionary(Text.from_string("xy"), Alphabet(tuple("ab")),
                                Alphabet(tuple("xy")), Bounds("monoalphabetic", 1, 1, 1),
                                WordDictionary.from_strings(("ab",)), max_word_length=1)
    assert result.status == "UNSAT"


def test_unknown_is_not_unsat(monkeypatch):
    monkeypatch.setattr(z3.Solver, "check", lambda self: z3.unknown)
    monkeypatch.setattr(z3.Solver, "reason_unknown", lambda self: "timeout")
    result = recover_dictionary(Text.from_string("x"), Alphabet(("a",)), Alphabet(("x",)),
                                Bounds("monoalphabetic", 1, 1, 1), WordDictionary.from_strings(("a",)))
    assert result.status == "UNKNOWN" and result.reason_unknown == "timeout"
    assert result.encoder is None and result.plaintext is None and not result.verified


def test_tokenized_dictionary_and_empty_ciphertext():
    vocabulary = WordDictionary((("ch",), ("qo", "ch")))
    result = recover_dictionary(Text((("x",),)), Alphabet(("ch", "qo")), Alphabet(("x", "y")),
                                Bounds("monoalphabetic", 1, 1, 1), vocabulary)
    assert result.status == "SAT" and result.plaintext == Text((("ch",),))
    empty = recover_dictionary(Text(()), Alphabet(("a",)), Alphabet(("x",)),
                               Bounds("monoalphabetic", 1, 1, 1), WordDictionary.from_strings(("a",)))
    assert empty.status == "SAT" and empty.verified


@pytest.mark.parametrize("kwargs", [{"timeout_ms": 0}, {"min_word_length": 0},
                                     {"min_word_length": 2, "max_word_length": 1}])
def test_invalid_public_bounds(kwargs):
    with pytest.raises(ValueError):
        recover_dictionary(Text.from_string("x"), Alphabet(("a",)), Alphabet(("x",)),
                           Bounds("monoalphabetic", 1, 1, 1), WordDictionary.from_strings(("a",)), **kwargs)


@pytest.mark.parametrize("representation", ["ite", "array", "interval", "chunk", "finite"])
def test_dictionary_solver_matches_exhaustive_python_oracle(representation):
    """Validate SAT/UNSAT and existence-preserving reductions without a Z3 oracle."""
    pa, ca = Alphabet(tuple("abc")), Alphabet(tuple("xy"))
    dictionary = WordDictionary.from_strings(("a", "ab"))
    codes = [(s,) for s in "xy"] + list(product("xy", repeat=2))
    possible_ciphertexts = set()
    for assignment in product(codes, repeat=3):
        try:
            encoder = Encoder({s: (code,) for s, code in zip(pa.symbols, assignment)})
        except ValueError:
            continue
        for words in product(dictionary.words, repeat=2):
            text = Text(words)
            possible_ciphertexts.add(encoder.encode(text, (0,) * text.size).words)
    for words in product(codes, repeat=2):
        ciphertext = Text(words)
        result = recover_dictionary(ciphertext, pa, ca, Bounds("verbose", 1, 1, 2),
                                    dictionary, representation=representation)
        assert result.status == ("SAT" if words in possible_ciphertexts else "UNSAT")


@pytest.mark.parametrize("representation", ["interval", "chunk", "finite"])
def test_unobserved_letters_consume_capacity_and_receive_complete_codes(representation):
    dictionary = WordDictionary.from_strings(("a",))
    result = recover_dictionary(Text.from_string("x"), Alphabet(tuple("abc")),
                                Alphabet(tuple("xy")), Bounds("verbose", 1, 1, 2),
                                dictionary, representation=representation)
    assert result.status == "SAT" and result.verified
    assert result.capacity["completed_unobserved_letters"] == 2
    assert result.encoder.codebook == {"a": (("x",),), "b": (("y", "x"),), "c": (("y", "y"),)}
    impossible = recover_dictionary(Text.from_string("x"), Alphabet(tuple("abcd")),
                                    Alphabet(tuple("xy")), Bounds("verbose", 1, 1, 2),
                                    dictionary, representation=representation)
    assert impossible.status == "UNSAT"


@pytest.mark.parametrize("representation", ["interval", "chunk", "finite"])
def test_unary_alphabet_completion(representation):
    result = recover_dictionary(Text(()), Alphabet(("a",)), Alphabet(("x",)),
                                Bounds("verbose", 1, 1, 3), WordDictionary.from_strings(("a",)),
                                representation=representation)
    assert result.status == "SAT" and result.verified
    assert result.encoder.codebook == {"a": (("x", "x", "x"),)}
