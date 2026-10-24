"""Conditional key facts justified by prefix-free decoding and fixed homophone sets."""
from voynich_smt.models.text import Text


def forced_cycle_conflicts(ciphertext, encoder, symbols):
    """Certify start-of-word cycles only until any ambiguous internal occurrence.

    A known prefix-free code at word start must be that letter's first codeword.
    If there are no internal occurrences, there can be no hidden intervening
    appearances of the letter. Certificates allow every cyclic key rotation.
    """
    conflicts = []
    for symbol in symbols:
        codes = encoder.codebook[symbol]
        if len(codes) < 2:
            continue
        seen = []
        for wi, word in enumerate(ciphertext.words):
            if any(word[i:i + len(code)] == code for code in codes for i in range(1, len(word))):
                break  # A different code could cross this occurrence: do not infer its count.
            match = next((i for i, code in enumerate(codes) if word[:len(code)] == code), None)
            if match is not None:
                seen.append((wi, match))
            if not any(all(choice == (i + r) % len(codes) for i, (_, choice) in enumerate(seen))
                       for r in range(len(codes))):
                conflicts.append({"symbol": symbol, "word_indices": [i for i, _ in seen],
                    "code_indices": [i for _, i in seen], "codes": [list(codes[i]) for _, i in seen],
                    "reason": "forced word-start appearances violate every cyclic rotation"})
                break
    return conflicts


def fixed_word_conflicts(ciphertext, encoder, symbols, dictionary, min_word_length=1, max_word_length=None):
    """Complete decodings survive other key changes while these owners stay fixed."""
    pinned = set(symbols)
    maximum = max_word_length or max(map(len, dictionary.words))
    conflicts = []
    for wi, word in enumerate(ciphertext.words):
        try:
            decoded = encoder.decode(Text((word,))).words[0]
        except ValueError:
            continue
        owners = set(decoded)
        if owners <= pinned and (decoded not in dictionary.words
                                 or not min_word_length <= len(decoded) <= maximum):
            conflicts.append({"word_index": wi, "decoded": list(decoded),
                "pinned_symbols": sorted(owners), "reason": "fixed decoding violates the language bounds"})
    return conflicts


