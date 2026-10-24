"""Audited cached thematic Latin passage extraction and fixed-window filters."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup

from benchmarks.eva_tokenization import screen, grouped_word
from benchmarks.historical_word_lengths import checksum, lexical_tokens

RAW = Path('data/raw/historical-comparanda')
OUT = Path('experiments/results/thematic-latin-passages')
INCIPITS = ('Carmine divinas','Maximus Iliacae','In nova','Quid tam','Hic alius')


def tokens(text, diagrams=False):
    """Unknown editorial content interrupts a passage; no spelling repairs."""
    text=re.sub(r'\[[^\]]*\]', ' § ', text)
    text=text.replace('*',' § ')
    if diagrams:text=re.sub(r'\b[A-Z]\b',' § ',text)
    return list(lexical_tokens(text))


def extract(name, raw):
    soup=BeautifulSoup(raw.decode('utf-8'),'html.parser')
    for tag in soup.select('script,style,sup'):tag.replace_with(' § ')
    if name=='emerald':
        body=soup.select_one('.mw-parser-output .text ol')
        if body is None:raise ValueError('Missing Emerald statements')
        items=body.find_all('li',recursive=False)
        if len(items)!=15:raise ValueError('Expected fifteen Emerald statements')
        texts=[t.get_text(' ',strip=True) for t in items]
        if not texts[0].startswith('VERUM SINE MENDACIO') or not texts[-1].startswith('COMPLETUM EST'):
            raise ValueError('Emerald endpoints changed')
        return [tokens(t) for t in texts],{'statement_boundaries':15,'excluded_header':True}
    if name=='sphaera':
        body=soup.select_one('.mw-parser-output')
        if body is None:raise ValueError('Missing Sphaera body')
        active=False;segments=[];pending=[];headings=0
        for p in body.find_all('p'):
            text=p.get_text(' ',strip=True)
            if 'Intentio nostra' in text and not active:
                active=True;text=text[text.index('Intentio nostra'):]
            if not active:continue
            if re.fullmatch(r'\[Cap\.\s*\d+\.\]',text):
                if pending:segments.append(pending);pending=[]
                headings+=1;continue
            if text:pending.extend(tokens(text,diagrams=True))
        if pending:segments.append(pending)
        if not segments or 'semidiametrorum' not in body.get_text():raise ValueError('Sphaera endpoints absent')
        return segments,{'chapter_breaks_after_incipit':headings,'excluded_header':True,'diagram_single_capitals_quarantined':True}
    if name.startswith('manilius'):
        ordinal=int(name[-1]);active=False;segments=[];pending=[]
        for p in soup.find_all('p'):
            text=p.get_text(' ',strip=True)
            if text.startswith(INCIPITS[ordinal-1]):active=True
            if not active:continue
            if 'Manilius The Miscellany' in text:break
            if text and not re.search(r'[A-Za-z]',text):
                if pending:segments.append(pending);pending=[]
                continue
            if text:pending.extend(tokens(text))
        if pending:segments.append(pending)
        if not segments:raise ValueError('Missing Manilius incipit')
        return segments,{'book':ordinal,'excluded_header_and_footer':True,
                         'caveat':'Classical verse sensitivity source; apparent transcription errors retained, not corrected or claimed diplomatic.'}
    raise ValueError('Unsupported source')


def run():
    selection=json.loads(Path('experiments/results/cross-window-passages/selection.json').read_text())
    inventory=json.loads(Path('experiments/configs/latin-contractions.json').read_text())
    manifest=json.loads(Path('data/processed/historical-comparanda/frequencies.json').read_text())
    report={'selection_sha256':checksum(selection),'inventory_sha256':checksum(inventory),
        'frequency_manifest_sha256':checksum(manifest),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'normalization':'Historical spelling and u/v, j/i retained; accents/ligatures follow existing lexical_tokens; no lemmatization. Numbers, brackets, asterisks and explicit chapter/book/statement boundaries interrupt windows. Isolated uppercase diagram letters in Sphaera interrupt windows; ordinary paragraph and verse-line boundaries may be crossed.',
        'audit':[],'rows':[],'solver_calls':0,'complete':False}
    OUT.mkdir(parents=True,exist_ok=True)
    sources=[]
    for name,identifier in [('emerald','emerald-tablet'),('sphaera','grosseteste-de-sphaera')]:
        raw=(RAW/(name+'.html')).read_bytes();segments,audit=extract(name,raw)
        metadata={'id':identifier,'raw_path':str(RAW/(name+'.html')),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'status':'accepted_exploratory','extraction':audit}
        sources.append((identifier,segments,[metadata]));report['audit'].append(metadata)
    all_segments=[];parts=[]
    for n in range(1,6):
        name=f'manilius{n}';raw=(RAW/(name+'.html')).read_bytes();segments,audit=extract(name,raw)
        all_segments.extend(segments);parts.append({'raw_path':str(RAW/(name+'.html')),
            'raw_sha256':hashlib.sha256(raw).hexdigest(),'extraction':audit})
    sources.append(('manilius-astronomica',all_segments,parts))
    report['audit'].append({'id':'manilius-astronomica','status':'accepted_sensitivity','parts':parts})
    turba=(RAW/'turba-latin.html').read_bytes()
    report['audit'].append({'id':'turba-philosophorum','status':'quarantined','raw_sha256':hashlib.sha256(turba).hexdigest(),
        'reason':'Previous incipit-to-FINISH extraction includes English prose after Latin; mixed recension compilation and unresolved abbreviated forms such as sententiasq; and eamq;. No reliable Latin endpoint or expansions guessed. Earlier Latin-labeled frequency/repetition figures must not be interpreted as Latin.'})
    for identifier,segments,metadata in sources:
        artifact={'source_id':identifier,'sources':metadata,'segments':segments,'records_sha256':checksum(segments)}
        (OUT/(identifier+'-segments.json')).write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
        for w in selection['windows']:
            atomic=tuple(map(tuple,w['atomic_words']));grouped=tuple(grouped_word(x) for x in atomic)
            for profile in ('letters','bounded-seven'):
                rules=[r for r in inventory['rules'] if r['id'] in inventory['profiles'][profile]]
                row={'window_id':w['id'],'source_id':identifier,'profile':profile,'records_sha256':checksum(segments)}
                for mode,cipher in [('atomic',atomic),('grouped',grouped)]:
                    m=screen(segments,cipher,rules);m.pop('minimum_unit_total_histogram');row[mode]=m
                report['rows'].append(row)
        print(identifier,'tokens',sum(x is not None for s in segments for x in s),
              'segments',len(segments),'barriers',sum(x is None for s in segments for x in s),flush=True)
    report['complete']=True
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':run()
