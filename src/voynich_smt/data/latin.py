"""Explicit Latin conventions; punctuation creates boundaries, never joins words."""
from dataclasses import asdict, dataclass
import re
import unicodedata

from .corpus import Corpus


@dataclass(frozen=True)
class LatinNormalization:
    lowercase: bool = True
    j_to_i: bool = True
    uv: str = 'preserve'
    strip_diacritics: bool = True
    alphabet: str = 'abcdefghiklmnopqrstuvxyz'
    preserve_spaces: bool = True

    def __post_init__(self):
        if self.uv not in {'preserve', 'v_to_u', 'u_to_v'}:
            raise ValueError('Invalid u/v convention')
        if not self.alphabet or len(set(self.alphabet)) != len(self.alphabet):
            raise ValueError('Alphabet must be nonempty and unique')
        if any(not c.isalpha() for c in self.alphabet):
            raise ValueError('Alphabet must contain letters only')
        if any(type(getattr(self, k)) is not bool for k in ('lowercase', 'j_to_i', 'strip_diacritics', 'preserve_spaces')):
            raise ValueError('Latin switches must be Boolean')


def normalize(source, raw, settings=LatinNormalization()):
    start = re.search(r'^\*\*\* START OF THE PROJECT GUTENBERG EBOOK.*$', raw, re.M)
    end = re.search(r'^\*\*\* END OF THE PROJECT GUTENBERG EBOOK.*$', raw, re.M)
    if not start or not end or start.end() >= end.start():
        raise ValueError('Missing or invalid Gutenberg body markers')
    first = re.search(r'^GALLIA est omnis', raw[start.end():end.start()], re.M)
    if not first:
        raise ValueError('Expected Caesar Latin incipit')
    body_start = start.end() + first.start()
    # Older Gutenberg editions include a prose footer before the formal marker.
    footer = re.search(r"^End of Project Gutenberg(?:'s)?[^\r\n]*", raw[body_start:end.start()], re.M)
    body_end = body_start + footer.start() if footer else end.start()
    records = []
    for match in re.finditer(r'[^\W\d_]+', raw[body_start:body_end], re.UNICODE):
        value = match.group()
        token = value.lower() if settings.lowercase else value
        if settings.strip_diacritics:
            token = ''.join(c for c in unicodedata.normalize('NFD', token) if unicodedata.category(c) != 'Mn')
        if settings.j_to_i:
            token = token.replace('j', 'i').replace('J', 'I')
        if settings.uv == 'v_to_u':
            token = token.replace('v', 'u').replace('V', 'U')
        elif settings.uv == 'u_to_v':
            token = token.replace('u', 'v').replace('U', 'V')
        accepted = all(c in settings.alphabet for c in token)
        records.append({'raw': value, 'tokens': list(token) if accepted else [],
                        'char_start': body_start + match.start(), 'char_end': body_start + match.end(),
                        'excluded_reason': None if accepted else 'outside configured alphabet'})
    # Book headings within the body are omitted explicitly, with source offsets retained.
    headings = [(m.start(), m.end()) for m in re.finditer(r'^C\. IULI CAESARIS.*COMMENTARIUS.*$', raw, re.M)]
    for r in records:
        if any(a <= r['char_start'] < b for a, b in headings):
            r['tokens'] = []
            r['excluded_reason'] = 'book heading'
    if not settings.preserve_spaces:
        joined = [g for r in records for g in r['tokens']]
        records = [{'raw': None, 'tokens': joined, 'char_start': body_start, 'char_end': body_end,
                    'excluded_reason': None, 'component_records': records}] if joined else []
    config = {**asdict(settings), 'parser_version': 2, 'body': 'Caesar incipit to prose footer or Gutenberg END',
              'body_char_start': body_start, 'body_char_end': body_end,
              'gutenberg_prose_footer': 'exclude when present',
              'punctuation': 'word separator', 'outside_alphabet': 'exclude whole word',
              'book_headings': 'exclude', 'offset_units': 'decoded Unicode characters'}
    return Corpus('latin', source, config, tuple(records))
