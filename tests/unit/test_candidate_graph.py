from voynich_smt.cipher.base import Bounds
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.text import Text


def test_strict_ciphertext_prefix_requires_strict_plaintext_prefix():
    graph = WordDictionary.from_strings(("ab", "ba")).candidate_graph(
        Text.from_string("xy xyz"), Bounds("verbose", 1, 1, 2), 1, 2)
    assert graph.candidates == ((), ())
    assert graph.pruned_candidates == 4


def test_arc_consistency_retains_all_supported_candidates():
    graph = WordDictionary.from_strings(("a", "b", "ab", "ba", "abc")).candidate_graph(
        Text.from_string("xy xyz"), Bounds("verbose", 1, 1, 2), 1, 3)
    assert graph.candidates == ((tuple("a"), tuple("b"), tuple("ab")),
                                (tuple("ab"), tuple("ba"), tuple("abc")))


def test_partial_ciphertext_prefix_does_not_force_decoded_symbol():
    graph = WordDictionary.from_strings(("a", "b")).candidate_graph(
        Text.from_string("xx xy"), Bounds("verbose", 1, 1, 2), 1, 1)
    assert graph.relations == ()
    assert graph.pruned_candidates == 0


def test_guaranteed_common_prefix_counts_atomic_tokens():
    graph = WordDictionary.from_strings(("a", "b", "ab", "ba")).candidate_graph(
        Text((("long-glyph", "other-glyph", "x"), ("long-glyph", "other-glyph", "y"))),
        Bounds("verbose", 1, 1, 2), 1, 2)
    assert graph.relations[0].shared_tokens == 1
    assert graph.relations[0].prefix is None
