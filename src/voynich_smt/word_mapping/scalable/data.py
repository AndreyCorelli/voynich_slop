"""Continuous fixtures: public cipher streams and separately serialized truth."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
import re
import unicodedata

from voynich_smt.data.corpus import digest, write_json

WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")


def tokenize(text):
    """Discard punctuation/sentence markers; character offsets stay private.

    ASCII modern-English scoring surface; apostrophe normalization preserves
    length. Hyphens/digits/non-ASCII letters separate tokens. This explicit
    lossy policy must not be described as original-spelling recovery.
    """
    normalized = text.replace('’', "'")
    matches = tuple(re.finditer(r"[A-Za-z]+(?:'[A-Za-z]+)*", normalized))
    return tuple(m.group().lower() for m in matches), tuple((m.start(), m.end()) for m in matches)


def surface(word, *, tokenization='english-continuous-v1'):
    if tokenization == 'ref-historical-continuous-v1':
        if (not isinstance(word, str) or not word or word != unicodedata.normalize('NFC', word.lower())
                or not word[0].isalpha() or not all(c.isalpha() or unicodedata.category(c).startswith('M') for c in word)):
            raise ValueError('Expected a normalized historical German surface word')
        return word
    if not isinstance(word, str) or WORD.fullmatch(word) is None:
        raise ValueError('Expected a normalized English surface word')
    return word


@dataclass(frozen=True)
class CipherStream:
    documents: tuple[tuple[int, ...], ...]
    type_count: int
    format_version: int = 1
    tokenization: str = 'english-continuous-v1'

    def __post_init__(self):
        object.__setattr__(self, 'documents', tuple(tuple(d) for d in self.documents))
        if self.format_version != 1 or self.tokenization not in {'english-continuous-v1', 'latin-iu-continuous-v1', 'ref-historical-continuous-v1'}:
            raise ValueError('Unsupported cipher contract')
        if type(self.type_count) is not int or self.type_count < 1 or not self.documents or any(not d for d in self.documents):
            raise ValueError('Expected nonempty documents and positive type count')
        observed = {w for d in self.documents for w in d}
        if any(type(w) is not int or not 0 <= w < self.type_count for d in self.documents for w in d) or observed != set(range(self.type_count)):
            raise ValueError('Expected dense observed opaque cipher IDs')

    @property
    def identity(self):
        return digest(asdict(self))

    def save(self, path):
        write_json(path, {**asdict(self), 'sha256': self.identity})

    @classmethod
    def load(cls, path):
        value = json.loads(Path(path).read_text())
        expected = {'documents', 'type_count', 'format_version', 'tokenization', 'sha256'}
        if set(value) != expected:
            raise ValueError('Unexpected fields in public cipher artifact')
        identity = value.pop('sha256')
        stream = cls(**value)
        if identity != stream.identity:
            raise ValueError('Cipher identity mismatch')
        return stream


@dataclass(frozen=True)
class CipherTruth:
    public_sha256: str
    plaintext: tuple[tuple[str, ...], ...]
    decoding: tuple[str, ...]
    key_seed: int
    format_version: int = 1

    def save(self, path):
        write_json(path, asdict(self))


def generate(documents, *, seed, tokenization="english-continuous-v1"):
    documents = tuple(tuple(surface(w, tokenization=tokenization) for w in d) for d in documents)
    if not documents or any(not d for d in documents):
        raise ValueError('Expected nonempty plaintext documents')
    words = sorted({w for d in documents for w in d})
    random.Random(seed).shuffle(words)
    ids = {w: i for i, w in enumerate(words)}
    public = CipherStream(tuple(tuple(ids[w] for w in d) for d in documents), len(words), tokenization=tokenization)
    return public, CipherTruth(public.identity, documents, tuple(words), seed)
