"""Reproducible synthetic generation with bounded boundary nulls."""

from dataclasses import asdict, replace
import random

from voynich_smt.cipher.base import Encoder, NullInsertion, generate_encoder
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.cipher.selection import choose


def generate(request, word_count: int, seed: int):
    if type(word_count) is not int or word_count <= 0 or type(seed) is not int:
        raise ValueError("Word count must be positive and seed must be an integer")
    maximum = request.max_word_length or max(map(len, request.dictionary.words))
    vocabulary = tuple(w for w in request.dictionary.words if request.min_word_length <= len(w) <= maximum)
    if not vocabulary:
        raise ValueError("No dictionary words satisfy the generation bounds")
    from voynich_smt.models.text import Text
    rng = random.Random(seed)
    plaintext = Text(tuple(rng.choice(vocabulary) for _ in range(word_count)))
    available_gaps = sum(len(w) + 1 for w in plaintext.words)
    target = min(request.nulls.max_occurrences, available_gaps * request.nulls.max_consecutive)
    distinct = min(request.nulls.max_distinct_symbols, target, len(request.ciphertext_alphabet.symbols) - 1)
    while distinct and ((len(request.ciphertext_alphabet.symbols) - distinct) ** request.bounds.max_code_length
                        < len(request.plaintext_alphabet.symbols) * request.bounds.max_homophones):
        distinct -= 1
    null_symbols = request.ciphertext_alphabet.symbols[-distinct:] if distinct else ()
    coding_alphabet = Alphabet(tuple(g for g in request.ciphertext_alphabet.symbols if g not in null_symbols))
    key = generate_encoder(request.plaintext_alphabet, coding_alphabet, request.bounds, seed + 1)
    encoder = Encoder(key.codebook, null_symbols)
    choices = choose(plaintext, encoder, request.selection, seed + 2)
    clean = encoder.encode(plaintext, choices)
    boundaries = []
    cursor = 0
    for wi, word in enumerate(plaintext.words):
        position = 0
        boundaries.append((wi, position))
        for symbol in word:
            position += len(encoder.codebook[symbol][choices[cursor]])
            boundaries.append((wi, position))
            cursor += 1
    buckets = {boundary: [] for boundary in boundaries}
    rng = random.Random(seed + 3)
    if null_symbols:
        for i in range(target):
            available = [b for b in boundaries if len(buckets[b]) < request.nulls.max_consecutive]
            boundary = rng.choice(available)
            glyph = null_symbols[i] if i < distinct else rng.choice(null_symbols)
            buckets[boundary].append(glyph)
    insertions = []
    for wi, word in enumerate(clean.words):
        observed_position = 0
        for ci in range(len(word) + 1):
            for glyph in buckets.get((wi, ci), ()):
                insertions.append(NullInsertion(wi, observed_position, glyph))
                observed_position += 1
            if ci < len(word):
                observed_position += 1
    ciphertext = encoder.encode(plaintext, choices, tuple(insertions))
    if encoder.decode(ciphertext) != plaintext:
        raise RuntimeError("Synthetic generator failed reverse verification")
    public = replace(request, ciphertext=ciphertext)
    truth = {"plaintext": asdict(plaintext), "encoder": asdict(encoder), "choices": choices,
             "nulls": [asdict(n) for n in insertions],
             "generator": {"version": "boundary-nulls-v1", "word_count": word_count,
                           "plaintext_seed": seed, "key_seed": seed + 1,
                           "choice_seed": seed + 2, "null_seed": seed + 3,
                           "selection": asdict(request.selection)}}
    return public, truth
