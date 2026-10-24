from itertools import product

import pytest

from voynich_smt.cipher.base import Bounds, Encoder, NullInsertion
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.metrics.complexity import measurements, weighted_score
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import NullBounds, Optimization, ComplexityWeights
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import recover, recover_dictionary


@pytest.mark.parametrize("optimization", [Optimization(), Optimization(True), Optimization(True, "weighted")])
def test_known_and_hidden_null_recovery(optimization):
    args = (Text.from_string("aa"), Text.from_string("xnx"), Alphabet(("a",)), Alphabet(tuple("xn")),
            Bounds("monoalphabetic", 1, 1, 1))
    nulls = NullBounds(True, 1, 1, 1)
    result = recover(*args, nulls=nulls, optimization=optimization)
    assert result.status == "SAT" and result.verified
    assert result.nulls == (NullInsertion(0, 1, "n"),)
    assert result.code_spans == (((0, 1), (2, 3)),)
    assert result.encoder.decode(args[1]) == args[0]
    hidden = recover_dictionary(*args[1:], WordDictionary.from_strings(("aa",)),
                                nulls=nulls, optimization=optimization)
    assert hidden.status == "SAT" and hidden.verified
    if optimization.enabled:
        assert result.optimization["optimality_proven"] and hidden.optimization["optimality_proven"]


@pytest.mark.parametrize("budget", [NullBounds(True, 0, 1, 1), NullBounds(True, 1, 0, 1),
                                    NullBounds(True, 1, 1, 0), NullBounds()])
def test_null_limits_force_unsat(budget):
    result = recover(Text.from_string("aa"), Text.from_string("xnx"), Alphabet(("a",)),
                     Alphabet(tuple("xn")), Bounds("monoalphabetic", 1, 1, 1), nulls=budget)
    assert result.status == "UNSAT"


def test_two_null_types_and_consecutive_bounds():
    args = (Text.from_string("aa"), Text.from_string("xnmx"), Alphabet(("a",)),
            Alphabet(tuple("xnm")), Bounds("monoalphabetic", 1, 1, 1))
    assert recover(*args, nulls=NullBounds(True, 2, 2, 2)).verified
    assert recover(*args, nulls=NullBounds(True, 1, 2, 2)).status == "UNSAT"
    assert recover(*args, nulls=NullBounds(True, 2, 2, 1)).status == "UNSAT"


def test_null_runs_reset_at_word_boundaries():
    result = recover(Text.from_string("a a"), Text.from_string("xn nx"), Alphabet(("a",)),
                     Alphabet(tuple("xn")), Bounds("monoalphabetic", 1, 1, 1),
                     nulls=NullBounds(True, 1, 2, 1))
    assert result.status == "SAT" and result.verified


def test_leading_nulls_do_not_trigger_raw_prefix_pruning():
    result = recover_dictionary(Text.from_string("nx ny"), Alphabet(tuple("ab")),
                                Alphabet(tuple("xyn")), Bounds("monoalphabetic", 1, 1, 1),
                                WordDictionary.from_strings(("a", "b")), nulls=NullBounds(True, 1, 2, 1))
    assert result.status == "SAT" and result.verified
    assert result.plaintext.words[0] != result.plaintext.words[1]


def test_interior_nulls_are_not_part_of_this_family():
    result = recover(Text.from_string("aa"), Text.from_string("xnyxy"), Alphabet(("a",)),
                     Alphabet(tuple("xyn")), Bounds("verbose", 1, 2, 2), nulls=NullBounds(True, 1, 1, 1))
    assert result.status == "UNSAT"


def test_zero_nulls_and_atomic_glyphs():
    result = recover(Text((("a", "a"),)), Text((("ch", "qo", "ch"),)), Alphabet(("a",)),
                     Alphabet(("ch", "qo")), Bounds("monoalphabetic", 1, 1, 1),
                     nulls=NullBounds(True, 1, 1, 1))
    assert result.verified
    assert result.nulls[0].symbol == "qo"
    empty = recover(Text(()), Text(()), Alphabet(("a",)), Alphabet(("x",)),
                    Bounds("monoalphabetic", 1, 1, 1), optimization=Optimization(True))
    assert empty.verified and empty.optimization["optimality_proven"]


def test_unobserved_codes_are_really_optimized():
    result = recover(Text.from_string("a"), Text.from_string("xy"), Alphabet(tuple("abc")),
                     Alphabet(tuple("xy")), Bounds("verbose", 1, 1, 2), optimization=Optimization(True))
    assert result.verified and result.optimization["optimality_proven"]
    assert result.complexity["raw"]["total_codebook_glyphs"] == 5
    assert sorted(len(cs[0]) for cs in result.encoder.codebook.values()) == [1, 2, 2]


def test_known_partial_domains_with_nulls():
    result = recover(Text.from_string("ab"), Text.from_string("xny"), Alphabet(tuple("ab")),
                     Alphabet(tuple("xyn")), Bounds("monoalphabetic", 1, 1, 1),
                     domains={1: ("a", "b")}, nulls=NullBounds(True, 1, 1, 1))
    assert result.verified and result.plaintext == Text.from_string("ab")


@pytest.mark.parametrize("method", ["lexicographic", "weighted"])
def test_optimizer_matches_exhaustive_python_oracle(method):
    # Includes both a genuine null explanation and a zero-null alternative.
    ciphertext = Text.from_string("xnx")
    dictionary = WordDictionary.from_strings(("aa", "ab"))
    weights = ComplexityWeights(mappings=2, extra_code_glyphs=5, distinct_null_symbols=0, null_occurrences=0)
    candidates = []
    codes = [(g,) for g in "xny"] + list(product("xny", repeat=2))
    for chosen_null in ((), ("x",), ("n",)):
        for a, b in product(codes, repeat=2):
            try:
                encoder = Encoder({"a": (a,), "b": (b,)}, chosen_null)
                plaintext = encoder.decode(ciphertext)
                if not dictionary.accepts(plaintext):
                    continue
                insertions = tuple(NullInsertion(0, i, g) for i, g in enumerate(ciphertext.words[0]) if g in chosen_null)
                if len(insertions) > 1 or encoder.encode(plaintext, (0,) * plaintext.size, insertions) != ciphertext:
                    continue
                raw = measurements(encoder, insertions)
                candidates.append(weighted_score(raw, weights) if method == "weighted" else
                                  tuple(raw[k] for k in ("distinct_null_symbols", "null_occurrences",
                                                        "additional_homophones", "total_codebook_glyphs")))
            except ValueError:
                continue
    result = recover_dictionary(ciphertext, Alphabet(tuple("ab")), Alphabet(tuple("xny")),
                                Bounds("verbose", 1, 1, 2), dictionary,
                                nulls=NullBounds(True, 1, 1, 1), optimization=Optimization(True, method, weights))
    assert result.verified and result.optimization["optimality_proven"]
    observed = result.complexity["weighted_score"] if method == "weighted" else tuple(
        item["value"] for item in result.optimization["objectives"])
    assert observed == min(candidates)
    assert result.complexity["raw"]["null_occurrences"] == (1 if method == "weighted" else 0)


def test_disabled_optimization_still_uses_configured_score_weights():
    result = recover(Text.from_string("a"), Text.from_string("x"), Alphabet(("a",)), Alphabet(("x",)),
                     Bounds("monoalphabetic", 1, 1, 1),
                     optimization=Optimization(weights=ComplexityWeights(mappings=7)))
    assert result.complexity["weighted_score"] == 7
