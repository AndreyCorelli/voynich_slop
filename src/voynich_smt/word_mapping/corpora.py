"""Ordered surface streams; exclusions are records, never silently removed."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import unicodedata

from voynich_smt.data.corpus import Corpus, digest, write_json


@dataclass(frozen=True)
class Normalization:
    lowercase: bool = True
    j_to_i: bool = True
    v_to_u: bool = True
    strip_diacritics: bool = True

    def apply(self, word):
        if self.lowercase:
            word = word.lower()
        if self.strip_diacritics:
            word = ''.join(c for c in unicodedata.normalize('NFD', word)
                           if unicodedata.category(c) != 'Mn')
        if self.j_to_i:
            word = word.replace('j', 'i')
        if self.v_to_u:
            word = word.replace('v', 'u')
        return word


@dataclass(frozen=True)
class WordRecord:
    source_id: str
    record_index: int
    original: str | None
    surface: str | None
    segment_id: str
    boundary_before: str | None
    exclusion_reason: str | None
    metadata: dict

    def __post_init__(self):
        if not self.source_id or self.record_index < 0:
            raise ValueError('Invalid record identity')
        if self.surface is not None and (not self.surface or any(c.isspace() for c in self.surface)):
            raise ValueError('Surface must be a nonempty word')
        if self.surface is None and not self.exclusion_reason:
            raise ValueError('Excluded records need a reason')


@dataclass(frozen=True)
class WordStream:
    records: tuple[WordRecord, ...]
    provenance: dict
    format_version: int = 1

    def __post_init__(self):
        if self.format_version != 1:
            raise ValueError('Unsupported word stream version')
        identities = [(r.source_id, r.record_index) for r in self.records]
        if len(identities) != len(set(identities)):
            raise ValueError('Duplicate source records')

    @property
    def identity(self):
        return digest(asdict(self))

    def segments(self):
        """Return contiguous accepted runs without crossing any barrier."""
        result, current = [], []
        previous = None
        for record in self.records:
            key = (record.source_id, record.segment_id)
            if record.boundary_before or key != previous or record.surface is None:
                if current:
                    result.append(tuple(current))
                    current = []
            if record.surface is not None:
                current.append(record.surface)
            previous = key
        if current:
            result.append(tuple(current))
        return tuple(result)

    def select(self, predicate, *, description):
        # Retain excluded positions as barriers to avoid bridging selection gaps.
        records = tuple(r if predicate(r) else WordRecord(
            r.source_id, r.record_index, r.original, None, r.segment_id,
            r.boundary_before, 'outside split', r.metadata) for r in self.records)
        return WordStream(records, {**self.provenance, 'parent_sha256': self.identity,
                                    'selection': description})

    def save(self, path):
        write_json(path, {**asdict(self), 'sha256': self.identity})

    @classmethod
    def load(cls, path):
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        stream = cls(tuple(WordRecord(**r) for r in value['records']),
                     value['provenance'], value['format_version'])
        if value['sha256'] != stream.identity:
            raise ValueError('Word stream checksum mismatch')
        return stream


def from_corpus(corpus: Corpus, source_id, *, raw_text=None,
                normalization=Normalization(), cross_locus=False):
    """Use ordered records, not Corpus.sample (which can discard barriers).

    Latin raw offsets recover conservative sentence/paragraph boundaries. Without
    raw text, sentence boundaries are explicitly unavailable. EVA loci are layout
    boundaries; no sentence or missing Currier label is inferred.
    """
    if corpus.kind not in {'latin', 'voynich-eva'}:
        raise ValueError('Unsupported corpus kind')
    if not corpus.normalization.get('preserve_spaces', True):
        raise ValueError('Word boundaries must be preserved')
    result, segment, previous = [], 0, None
    for index, record in enumerate(corpus.records):
        boundary = 'source' if previous is None else None
        if corpus.kind == 'voynich-eva':
            if previous is not None:
                if record.get('folio') != previous.get('folio'):
                    boundary = 'folio'
                elif not cross_locus and record.get('locus') != previous.get('locus'):
                    boundary = 'locus'
            surface = ''.join(record['tokens']) if record['tokens'] else None
        else:
            if raw_text is not None:
                start, end = record.get('char_start'), record.get('char_end')
                if (not isinstance(start, int) or not isinstance(end, int)
                        or not 0 <= start < end <= len(raw_text)
                        or raw_text[start:end] != record['raw']):
                    raise ValueError('Latin offsets do not match raw text')
                if previous is not None:
                    if start < previous['char_end']:
                        raise ValueError('Latin records must be ordered')
                    gap = raw_text[previous['char_end']:start]
                    if re.search(r'[.!?]', gap):
                        boundary = 'sentence-punctuation'
                    elif re.search(r'\n\s*\n', gap):
                        boundary = 'paragraph'
            # Normalize retained raw word rather than an already folded spelling.
            surface = normalization.apply(record['raw']) if record['tokens'] else None
        if boundary:
            segment += 1
        metadata = {k: v for k, v in record.items() if k not in {'raw', 'tokens'}}
        result.append(WordRecord(source_id, index, record.get('raw'), surface,
                                 str(segment), boundary,
                                 record.get('excluded_reason') or ('empty token' if surface is None else None),
                                 metadata))
        previous = record
    return WordStream(tuple(result), {
        'corpus_sha256': corpus.identity, 'source': corpus.source,
        'upstream_normalization': corpus.normalization,
        'scoring_normalization': asdict(normalization) if corpus.kind == 'latin' else None,
        'boundary_policy': ('cross-locus' if cross_locus else 'locus')
        if corpus.kind == 'voynich-eva' else
        ('raw-offset-punctuation-and-paragraph' if raw_text is not None else 'sentence-unavailable'),
        'raw_text_sha256': digest(raw_text) if raw_text is not None else None,
    })


def from_segments(segments, source_id, *, source, normalization=Normalization()):
    """Adapt audited cached sequences. Their original punctuation is unavailable."""
    records = []
    for segment_id, words in enumerate(segments):
        for position, word in enumerate(words):
            records.append(WordRecord(source_id, len(records), word,
                normalization.apply(word) if word is not None else None,
                str(segment_id), 'source-segment' if position == 0 else None,
                'upstream discarded-token barrier' if word is None else None,
                {'position_in_segment': position}))
    return WordStream(tuple(records), {'source': source,
        'input_sha256': digest(segments), 'scoring_normalization': asdict(normalization),
        'boundary_policy': 'source-segments-and-barriers; sentence-unavailable',
        'original_spelling': 'cached stream spelling; prior normalization may be irreversible'})


def validate_splits(streams):
    """Reject physical overlap and exact duplicated accepted passages."""
    seen_records, seen_passages = {}, {}
    for name, stream in streams.items():
        for record in stream.records:
            if record.surface is None:
                continue
            key = (record.source_id, record.record_index)
            if key in seen_records:
                raise ValueError(f'Split overlap: {name} and {seen_records[key]}')
            seen_records[key] = name
        for segment in stream.segments():
            # Short common sentences are not sufficient evidence of duplicated prose.
            if len(segment) >= 10:
                key = digest(segment)
                if key in seen_passages and seen_passages[key] != name:
                    raise ValueError('Duplicated passage across splits')
                seen_passages[key] = name
    return {name: stream.identity for name, stream in streams.items()}
