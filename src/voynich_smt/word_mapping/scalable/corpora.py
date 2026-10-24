"""Preparation-only source adapters; sentence metadata never enters CipherStream."""
from dataclasses import dataclass

from .data import tokenize


@dataclass(frozen=True)
class PreparedDocument:
    source_id: str
    words: tuple[str, ...]
    sentence_ends: tuple[int, ...]  # Private alignment aid, not public input.


def read_ewt(lines):
    """Group official CoNLL-U text fields by newdoc, never reset at sentences.

    Dependency rows are deliberately unused; these normalized surfaces are not
    automatically aligned with UD syntactic word IDs, contractions or punctuation.
    Source/author identity remains preparation metadata.
    """
    source_id, words, ends = None, [], []
    for line in lines:
        if line.startswith('# newdoc id = '):
            if source_id is not None:
                if not words:
                    raise ValueError('Empty source document')
                yield PreparedDocument(source_id, tuple(words), tuple(ends))
            source_id = line.removeprefix('# newdoc id = ').strip()
            words, ends = [], []
        elif line.startswith('# text = '):
            if source_id is None:
                raise ValueError('Sentence without document identity')
            tokens, _ = tokenize(line.removeprefix('# text = ').rstrip('\r\n'))
            words.extend(tokens)
            ends.append(len(words))
    if source_id is not None:
        if not words:
            raise ValueError('Empty source document')
        yield PreparedDocument(source_id, tuple(words), tuple(ends))
