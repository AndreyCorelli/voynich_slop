"""Original-spelling DTA TEI extraction for independent historical benchmarks.

No modernized spellings, sentence labels or topic filtering are used.
"""
from collections import Counter
from dataclasses import dataclass
import re
import unicodedata
import xml.etree.ElementTree as ET

from .historical_german import normalize_surface

NS={'t':'http://www.tei-c.org/ns/1.0'}
GAP='\uffff'


@dataclass(frozen=True)
class DtaDocument:
    metadata: dict
    segments: tuple
    statistics: dict


def parse_dta(data):
    root=ET.fromstring(data)
    if root.tag!='{'+NS['t']+'}TEI':raise ValueError('Expected namespaced DTA TEI')
    body=root.find('./t:text/t:body',NS)
    if body is None:raise ValueError('Missing TEI main body')
    stats=Counter()
    def render(element):
        tag=element.tag.split('}')[-1]
        if tag in ('fw','note','figure'):
            stats['excluded_'+tag]+=1;return ''
        if tag=='gap':stats['gaps']+=1;return GAP
        if tag=='lb':return '\n' if element.get('break')!='no' else ''
        if tag=='pb':stats['pages']+=1;return ' '
        if tag=='choice':
            for name in ('orig','sic','abbr'):
                selected=element.find('t:'+name,NS)
                if selected is not None:
                    stats['choice_'+name]+=1
                    value=render(selected)
                    # DTABf orig/reg pairs can document a missing printed line-end
                    # hyphen: join the explicitly paired original word fragments.
                    if name=='orig' and element.find('t:reg',NS) is not None:
                        value=re.sub(r'\s*\n\s*','',value)
                    return value
            raise ValueError('Unsupported TEI choice without original reading')
        content=element.text or ''
        for child in element:
            content+=render(child)+(child.tail or '')
        if tag in ('p','head','div','cit','l','lg','bibl'):
            return ' '+content+' '
        return content
    text=render(body)
    # Join mechanically marked line wraps, including page furniture removed above.
    text,n=re.subn(r'[-¬]\s*\n\s*(?=[^\W\d_])','',text)
    stats['joined_line_hyphens']=n
    segments=[];current=[];word=[];skip_suffix=False
    def finish_word():
        if word:
            value=normalize_surface(''.join(word));word.clear()
            if value is None:raise ValueError('Invalid extracted Unicode word')
            current.append(value)
    for index,c in enumerate(text):
        if c==GAP:
            # Neither fragment of an illegible partial word is a real token.
            word.clear()
            if current:segments.append(tuple(current));current.clear()
            skip_suffix=index+1<len(text) and (text[index+1].isalpha() or unicodedata.category(text[index+1]).startswith('M'))
        elif c.isalpha() or (unicodedata.category(c).startswith('M') and word):
            if not skip_suffix:word.append(c)
        else:
            finish_word();skip_suffix=False
    finish_word()
    if current:segments.append(tuple(current))
    header=root.find('t:teiHeader',NS)
    def strings(path):return [' '.join(''.join(e.itertext()).split()) for e in header.findall(path,NS)]
    metadata={'title':strings('./t:fileDesc/t:sourceDesc/t:biblFull/t:titleStmt/t:title'),
        'authors':strings('./t:fileDesc/t:sourceDesc/t:biblFull/t:titleStmt/t:author'),
        'source_dates':strings('./t:fileDesc/t:sourceDesc/t:biblFull/t:publicationStmt/t:date'),
        'edition':strings('./t:fileDesc/t:editionStmt/t:edition'),
        'licenses':[e.get('target') for e in header.findall('.//t:licence',NS)],
        'source_description':strings('./t:fileDesc/t:sourceDesc/t:bibl'),
        'policy':'Original main body only; remove notes/page furniture/figures; choose orig/sic/abbr; supplied transcription retained; lowercase/NFC/long-s folding; preserve diacritics and abbreviations; digits/punctuation separate words; illegible gaps split streams.'}
    stats['segments']=len(segments);stats['tokens']=sum(map(len,segments));stats['longest_segment']=max(map(len,segments),default=0)
    stats['supplied_elements']=len(body.findall('.//t:supplied',NS))
    return DtaDocument(metadata,tuple(segments),dict(stats))
