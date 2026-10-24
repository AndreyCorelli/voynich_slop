"""Conservative IVTFF EVA 2.0 ingestion, retaining source loci and annotations."""
from dataclasses import asdict, dataclass
import re

from .corpus import Corpus


@dataclass(frozen=True)
class EvaNormalization:
    uncertain_spaces: str = 'split'
    annotated_words: str = 'exclude'
    tokenization: str = 'eva-characters'

    def __post_init__(self):
        if self.uncertain_spaces not in {'split', 'join', 'exclude-line'}:
            raise ValueError('Invalid uncertain-space policy')
        if self.annotated_words not in {'exclude', 'preserve'}:
            raise ValueError('Invalid annotated-word policy')
        if self.tokenization != 'eva-characters':
            raise ValueError('Only explicit EVA character units are implemented')


def _units(word):
    pattern = r'\[[^\]]*\]|\{[^}]*\}|@\d{3};|\?+|[a-zA-Z]|.'
    return re.findall(pattern, word)


def normalize(source, raw, settings=EvaNormalization()):
    if not raw.startswith('#=IVTFF Eva- 2.0'):
        raise ValueError('Expected IVTFF EVA 2.0')
    lines, pending = [], None
    for physical, value in enumerate(raw.splitlines(), 1):
        if not value or value.startswith('#'):
            continue
        if pending:
            if not value.startswith('/'):
                raise ValueError('Invalid IVTFF continuation')
            pending[1] += value[1:].rstrip('/')
            if not value.endswith('/'):
                lines.append(tuple(pending)); pending = None
        elif value.endswith('/'):
            pending = [physical, value[:-1]]
        else:
            lines.append((physical, value))
    if pending:
        raise ValueError('Unclosed IVTFF continuation')
    records, page = [], {}
    for physical, value in lines:
        match = re.match(r'^<([^>]+)>\s*(.*)$', value)
        if not match:
            raise ValueError(f'Unrecognized IVTFF line {physical}')
        identifier, body = match.groups()
        if '.' not in identifier:
            page = dict(re.findall(r'\$([A-Z])=([^\s>]+)', body))
            continue
        locus, _, transcriber = identifier.partition(';')
        folio = locus.split('.')[0]
        annotations = re.findall(r'<[^>]*>', body)
        # Text tags persist until the end of the page (or reset).
        for key, val in re.findall(r'<@([A-Z])=([^>]+)>', body):
            if val == '@':
                page.pop(key, None)
            else:
                page[key] = val
        clean = re.sub(r'<[\-~]>', '.', body)
        clean = re.sub(r'<[^>]*>', '', clean).strip()
        excluded_line = ',' in clean and settings.uncertain_spaces == 'exclude-line'
        clean = clean.replace(',', '.' if settings.uncertain_spaces != 'join' else '')
        for wi, word in enumerate(clean.split('.')):
            if not word:
                continue
            annotated = not bool(re.fullmatch('[a-z]+', word))
            reason = 'uncertain word space' if excluded_line else ('annotated or non-basic EVA word'
                      if annotated and settings.annotated_words == 'exclude' else None)
            records.append({'raw': word, 'raw_locus_text': body, 'tokens': _units(word) if reason is None else [],
                            'folio': folio, 'locus': locus, 'transcriber': transcriber or None,
                            'section': page.get('I'), 'page_variables': dict(page),
                            'physical_line': physical, 'word_in_locus': wi,
                            'annotations': annotations, 'uncertain_space_in_locus': ',' in body,
                            'excluded_reason': reason})
    config = {**asdict(settings), 'parser_version': 1, 'ligatures_and_alternatives': 'atomic annotations when preserved',
              'word_boundaries': 'period, configured comma, drawing interruptions',
              'eva_units_are_manuscript_glyphs': False}
    return Corpus('voynich-eva', source, config, tuple(records))
