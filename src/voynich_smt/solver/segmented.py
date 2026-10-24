"""Explicit oracle-boundary diagnostic, separate from ordinary hidden recovery."""


def validate_segmentation(ciphertext, bounds, segmentation):
    if len(segmentation) != len(ciphertext.words):
        raise ValueError('One boundary list is required per ciphertext word')
    rows = tuple(tuple(row) for row in segmentation)
    for word, row in zip(ciphertext.words, rows):
        if (len(row) < 2 or any(type(x) is not int for x in row)
                or row[0] != 0 or row[-1] != len(word)
                or any(not bounds.min_code_length <= b-a <= bounds.max_code_length
                       for a, b in zip(row, row[1:]))):
            raise ValueError('Invalid codeword boundaries')
    return rows


def recover_segmented(request, segmentation):
    if request.representation != 'finite' or request.nulls.enabled or request.optimization.enabled:
        raise ValueError('Boundary diagnostics require finite null-free feasibility')
    from .recovery import _recover, score_result
    result = _recover(None, request.ciphertext, request.plaintext_alphabet,
        request.ciphertext_alphabet, request.bounds, request.timeout_ms,
        dictionary=request.dictionary, min_word_length=request.min_word_length,
        max_word_length=request.max_word_length or max(map(len, request.dictionary.words)),
        selection=request.selection, dictionary_encoding=request.dictionary_encoding,
        known_segmentation=segmentation)
    return score_result(result, request.optimization)


def validate_word_lengths(ciphertext, bounds, word_lengths):
    lengths = tuple(word_lengths)
    if (len(lengths) != len(ciphertext.words)
            or any(type(n) is not int or n <= 0
                   or not n*bounds.min_code_length <= len(word) <= n*bounds.max_code_length
                   for word, n in zip(ciphertext.words, lengths))):
        raise ValueError('Invalid plaintext word lengths')
    return lengths


def recover_with_word_lengths(request, word_lengths, *, solver_backend="auto"):
    if request.representation != 'finite' or request.nulls.enabled or request.optimization.enabled:
        raise ValueError('Length diagnostics require finite null-free feasibility')
    from .recovery import _recover, score_result
    result = _recover(None, request.ciphertext, request.plaintext_alphabet,
        request.ciphertext_alphabet, request.bounds, request.timeout_ms,
        dictionary=request.dictionary, min_word_length=request.min_word_length,
        max_word_length=request.max_word_length or max(map(len, request.dictionary.words)),
        selection=request.selection, dictionary_encoding=request.dictionary_encoding,
        known_word_lengths=word_lengths, solver_backend=solver_backend)
    return score_result(result, request.optimization)
