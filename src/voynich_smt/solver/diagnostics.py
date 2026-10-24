"""Mask glyph evidence while retaining latent words, lengths, and cyclic state."""
from .recovery import _recover, score_result


def recover_observations(request, word_indices):
    if request.nulls.enabled or request.optimization.enabled or request.representation != "finite":
        raise ValueError("Masked diagnosis currently requires finite, null-free feasibility")
    indices = tuple(word_indices)
    if len(set(indices)) != len(indices):
        raise ValueError("Observed word indices must be unique")
    maximum = request.max_word_length or max(map(len, request.dictionary.words))
    result = _recover(None, request.ciphertext, request.plaintext_alphabet, request.ciphertext_alphabet,
                      request.bounds, request.timeout_ms, dictionary=request.dictionary,
                      min_word_length=request.min_word_length, max_word_length=maximum,
                      selection=request.selection, observed_words=indices,
                      dictionary_encoding=request.dictionary_encoding)
    return score_result(result, request.optimization)
