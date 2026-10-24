"""Dedicated word ciphers; truth is a separate evaluation-only artifact."""
from collections import Counter
from dataclasses import asdict, dataclass
import random

from voynich_smt.data.corpus import digest


@dataclass(frozen=True)
class CipherInput:
    segments: tuple[tuple[str, ...], ...]
    source: dict
    encoder: dict
    format_version: int = 1

    @property
    def identity(self):
        return digest(asdict(self))


@dataclass(frozen=True)
class CipherTruth:
    public_sha256: str
    plaintext: tuple[tuple[str, ...], ...]
    decoding: dict[str, str]
    deterministic_accuracy_ceiling: float


def generate(plaintext, *, source, seed, kind='one-to-one', homophones=2):
    plaintext = tuple(tuple(s) for s in plaintext)
    if not any(plaintext) or any(not isinstance(w, str) or not w or
            any(c.isspace() for c in w) for s in plaintext for w in s):
        raise ValueError('Fixture needs nonempty plaintext surface words')
    if kind not in {'one-to-one', 'homophonic', 'frequency-distorting', 'lossy'}:
        raise ValueError('Unsupported word cipher')
    if type(homophones) is not int or homophones < 1:
        raise ValueError('homophones must be positive')
    rng = random.Random(seed)
    vocabulary = sorted({w for s in plaintext for w in s})
    rng.shuffle(vocabulary)
    encodings, decoding = {}, {}
    for index, word in enumerate(vocabulary):
        count = 1 if kind in {'one-to-one', 'lossy'} else homophones
        if kind == 'frequency-distorting':
            count = rng.randint(1, homophones)
        forms = tuple(f'v{index // 2 if kind == "lossy" else index:05d}_{i}' for i in range(count))
        encodings[word] = forms
        if kind != 'lossy':
            decoding.update({form: word for form in forms})
    ciphertext = tuple(tuple(rng.choice(encodings[w]) for w in s) for s in plaintext)
    owners = {}
    for cipher_segment, plain_segment in zip(ciphertext, plaintext):
        for cipher, plain in zip(cipher_segment, plain_segment):
            owners.setdefault(cipher, Counter())[plain] += 1
    if kind == 'lossy':
        # Majority decoder is an oracle ceiling, never part of public search inputs.
        decoding = {cipher: sorted(counts, key=lambda w: (-counts[w], w))[0]
                    for cipher, counts in owners.items()}
    ceiling = sum(max(counts.values()) for counts in owners.values()) / sum(map(len, plaintext))
    public = CipherInput(ciphertext, source, {'kind': kind, 'seed': seed,
        'homophones': homophones, 'version': 1,
        'scope': 'out-of-model lossy stress test' if kind == 'lossy' else 'deterministic decoding'})
    truth = CipherTruth(public.identity, plaintext, decoding, ceiling)
    return public, truth
