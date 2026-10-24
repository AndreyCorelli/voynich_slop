"""Redundant public substring domains for mappings used in observed text."""


def substrings(ciphertext, bounds):
    return frozenset(word[i:i+size] for word in ciphertext.words for i in range(len(word))
        for size in range(bounds.min_code_length, min(bounds.max_code_length, len(word)-i)+1))


def recover_observed_codes(request, word_lengths=None):
    if request.representation != 'finite' or request.nulls.enabled or request.optimization.enabled:
        raise ValueError('Observed domains require finite null-free feasibility')
    from .recovery import _recover, score_result
    result = _recover(None, request.ciphertext, request.plaintext_alphabet,
        request.ciphertext_alphabet, request.bounds, request.timeout_ms,
        dictionary=request.dictionary, min_word_length=request.min_word_length,
        max_word_length=request.max_word_length or max(map(len, request.dictionary.words)),
        selection=request.selection, dictionary_encoding=request.dictionary_encoding,
        known_word_lengths=word_lengths, codeword_domains='observed')
    return score_result(result, request.optimization)
