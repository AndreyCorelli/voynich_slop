"""Conditional key-guided recovery; key hints do not enter ordinary public requests."""
from voynich_smt.cipher.base import Encoder
from .key_evidence import fixed_word_conflicts, forced_cycle_conflicts
from .recovery import _recover, score_result


def recover_guided(request, encoder, pinned_symbols=(), *, rotate=False,
                   hint_symbols=(), word_hints=None, minimize_core=False):
    if (request.representation != "finite" or request.nulls.enabled
            or request.optimization.enabled or request.selection.mode != "cycle"):
        raise ValueError("Guidance requires finite, null-free cyclic feasibility")
    if type(rotate) is not bool or type(minimize_core) is not bool:
        raise ValueError("Rotation and core minimization flags must be boolean")
    if encoder.null_symbols or set(encoder.codebook) != set(request.plaintext_alphabet.symbols):
        raise ValueError("Guide key must cover the full plaintext alphabet without nulls")
    # Revalidate mutable Encoder codebooks before using them as restrictions.
    Encoder(encoder.codebook)
    if any(not 1 <= len(cs) <= request.bounds.max_homophones or any(
            not request.bounds.min_code_length <= len(code) <= request.bounds.max_code_length
            or any(g not in request.ciphertext_alphabet.symbols for g in code) for code in cs)
            for cs in encoder.codebook.values()):
        raise ValueError("Guide key violates request bounds or cipher alphabet")
    pinned_symbols, hint_symbols = tuple(pinned_symbols), tuple(hint_symbols)
    for symbols in (pinned_symbols, hint_symbols):
        if len(set(symbols)) != len(symbols) or any(s not in encoder.codebook for s in symbols):
            raise ValueError("Guide symbols must be unique plaintext alphabet members")
    maximum = request.max_word_length or max(map(len, request.dictionary.words))
    words = {i: tuple(w) for i, w in (word_hints or {}).items()}
    for i, word in words.items():
        if (type(i) is not int or not 0 <= i < len(request.ciphertext.words)
                or word not in request.dictionary.words
                or not request.min_word_length <= len(word) <= maximum):
            raise ValueError("Invalid plaintext word hint")
    result = _recover(None, request.ciphertext, request.plaintext_alphabet,
        request.ciphertext_alphabet, request.bounds, request.timeout_ms,
        dictionary=request.dictionary, min_word_length=request.min_word_length,
        max_word_length=maximum, selection=request.selection,
        dictionary_encoding=request.dictionary_encoding,
        guidance={"encoder": encoder, "pinned_symbols": pinned_symbols, "rotate": rotate,
                  "hint_symbols": hint_symbols, "word_hints": words,
                  "minimize_core": minimize_core})
    return score_result(result, request.optimization)
