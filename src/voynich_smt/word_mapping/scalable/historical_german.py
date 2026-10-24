"""ReF CorA-XML surface adapter, independent of decipherment and hidden labels.

Use utf from tok_anno (source word segmentation, not normalized lemmas).
Preserve abbreviation/umlaut combining marks, u/v, i/j, and historical spelling.
Lowercase, NFC and long-s folding are declared benchmark transformations.
"""
from collections import Counter
from dataclasses import dataclass
import re
import unicodedata
import xml.etree.ElementTree as ET

TOKENIZATION = 'ref-historical-continuous-v1'


def normalize_surface(value):
    value = unicodedata.normalize('NFC', value.replace('ſ', 's').replace('\u200d', '').lower())
    if value and value[0].isalpha() and all(c.isalpha() or unicodedata.category(c).startswith('M') for c in value):
        return value
    return None


@dataclass(frozen=True)
class RefDocument:
    identifier: str
    metadata: dict
    segments: tuple
    statistics: dict
    annotations: tuple


def parse_cora(data):
    root = ET.fromstring(data)
    if root.tag != 'text' or root.find('cora-header') is None:
        raise ValueError('Expected ReF CorA-XML, not TIGER or arbitrary XML')
    metadata = dict(line.split(': ', 1) for line in (root.findtext('header') or '').splitlines() if ': ' in line)
    metadata = {k: v.strip() for k,v in metadata.items()}
    tokens = root.findall('token'); ids = {t.get('id'):i for i,t in enumerate(tokens)}
    if len(ids)!=len(tokens) or None in ids:
        raise ValueError('Missing or duplicate source token ID')
    # Page jumps reveal noncontiguous excerpt joins. Printed lines/columns and
    # ordinary supported punctuation never introduce sentence resets.
    breaks = set(); previous = None; stats = Counter()
    for page in root.findall('./layoutinfo/page'):
        number = page.get('no',''); match = re.fullmatch(r'(\d+)',number)
        if not match:
            stats['unparsed_page_labels']+=1; previous=None; continue
        current = int(match.group(1))
        if previous is not None and (current<previous or current>previous+1):
            col_ids = page.get('range','').split('..')
            column = root.find(f"./layoutinfo/column[@id='{col_ids[0]}']")
            line = None if column is None else root.find(f"./layoutinfo/line[@id='{column.get('range','').split('..')[0]}']")
            first = None if line is None else line.get('range','').split('..')[0].split('_')[0]
            if first in ids:
                breaks.add(ids[first]);stats['page_discontinuities']+=1
            else:
                raise ValueError('Cannot locate discontinuous page boundary')
        previous=current
    segments=[]; current=[]; annotations=[]
    def flush():
        if current:segments.append(tuple(current));current.clear()
    for index,token in enumerate(tokens):
        if index in breaks:flush()
        children=token.findall('tok_anno')
        if not children:
            flush();stats['missing_annotation_token_barriers']+=1;continue
        for child in children:
            stats['annotation_tokens']+=1; raw=child.get('utf')
            if raw is None:flush();stats['missing_utf_barriers']+=1;continue
            word=normalize_surface(raw)
            if word is None:
                # Supported pure punctuation is discarded; ambiguous question,
                # bracket and asterisk notation is conservatively a gap.
                # Unreadable/part-word/number/symbol tokens are conservative gaps.
                if raw and all(unicodedata.category(c).startswith('P') for c in raw) and not any(c in raw for c in '[]?*'):
                    stats['punctuation_removed']+=1
                else:flush();stats['unsupported_surface_barriers']+=1
                continue
            current.append(word);stats['surface_tokens']+=1
            annotations.append({'source_token':token.get('id'),'annotation_token':child.get('id'),
                'segment':len(segments),'offset':len(current)-1,'surface':word,'utf':raw,
                **{name:child.find(name).get('tag') if child.find(name) is not None else None
                   for name in ('lemma','lemmaId','pos','morph','annoType')}})
    flush()
    stats['segments']=len(segments);stats['longest_segment']=max(map(len,segments),default=0)
    return RefDocument(root.get('id'),metadata,tuple(segments),dict(stats),tuple(annotations))
