"""Broaden attested medieval Latin windows with unchanged contraction diagnostics."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re
from html.parser import HTMLParser

from benchmarks.historical_length_sources import fetch
from benchmarks.historical_word_lengths import source, lexical_tokens
from benchmarks.latin_contractions import CONFIG, checksum, validate_inventory
from benchmarks.latin_length_failures import diagnose

OUT=Path('experiments/results/expanded-medieval-latin')
WORKS=[
 {'id':'einhard','title':'Vita Karoli Magni','period':'9th century','genre':'biography',
  'parts':[('latin-expanded-einhard.html','https://www.thelatinlibrary.com/ein.html')],
  'start':'Vitam et conversationem'},
 {'id':'gesta','title':'Gesta Francorum, books I–X','period':'early 12th century','genre':'crusade narrative',
  'parts':[(f'latin-expanded-gesta-{n}.html',f'https://www.thelatinlibrary.com/gestafrancorum/gestafrancorum{n}.shtml') for n in range(1,11)],'start':None},
 {'id':'bury','title':'Philobiblon','period':'14th century','genre':'treatise on books and learning',
  'parts':[('latin-expanded-bury.html','https://www.thelatinlibrary.com/debury.html')],
  'start':'UNIVERSIS Christi fidelibus'},
 {'id':'dante','title':'Monarchia, books I–III','period':'early 14th century','genre':'political philosophy',
  'parts':[(f'latin-expanded-dante-{n}.html',f'https://www.thelatinlibrary.com/dante/mon{n}.shtml') for n in range(1,4)],'start':None},
]


class Paragraphs(HTMLParser):
    """Treat each new p as a boundary even when legacy HTML forgets its closing tag."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[];self.current=None;self.ignored=0
    def flush(self):
        if self.current is not None:self.rows.append(self.current)
        self.current=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='p':
            self.flush();self.current={'text':'','classes':attrs.get('class','').split(),'links':[]}
        elif tag in {'script','style','sup'}:self.ignored+=1
        elif tag=='a' and self.current is not None:
            self.current['links'].append(attrs.get('href',''))
        elif tag=='br' and self.current is not None:self.current['text']+=' '
    def handle_endtag(self,tag):
        if tag=='p':self.flush()
        elif tag in {'script','style','sup'}:self.ignored=max(0,self.ignored-1)
    def handle_data(self,data):
        if self.current is not None and not self.ignored:self.current['text']+=data
    def close(self):
        super().close();self.flush()


def extract_html(raw, encoding, kind, incipit=None):
    try:
        decoded=raw.decode(encoding);encoding_used=encoding
    except UnicodeDecodeError:
        decoded=raw.decode('windows-1252');encoding_used='windows-1252'
    parser=Paragraphs();parser.feed(decoded);parser.close()
    words=[];started=False;footer=False;skip_title=False;paragraphs=0
    for p in parser.rows:
        text=p['text'].strip()
        if any(re.search(r'(?:^|/)medieval\.html$',url) for url in p['links']):
            footer=True;break
        if set(p['classes']) & {'pagehead','margin','border','smallborder'}:
            continue
        if not text:continue
        if not started:
            if incipit is not None:
                started=text.startswith(incipit)
            elif kind=='gesta':
                started=bool(re.match(r'^\[\s*[ivxlcdm]+\s*\]',text,re.I))
            elif kind=='dante':
                started=bool(re.match(r'^[IVXLCDM]+\.\s*1\.',text))
            if not started:continue
        if skip_title:
            words.append(None);skip_title=False;continue
        if re.match(r'^Capitulum\s+[IVXLCDM]+\b',text,re.I):
            words.append(None);skip_title=True;continue
        if re.match(r'^(?:Explicit|Explicet|Incipiunt)\b',text,re.I):
            words.append(None);continue
        # Original whitespace is retained across inline tags; no extra word breaks.
        if kind in {'einhard','gesta'}:
            text=re.sub(r'^\[\s*(?:[ivxlcdm]+|\d+)\s*\]\s*','§ ',text,flags=re.I)
        if kind=='dante':
            text=re.sub(r'^[IVXLCDM]+\.\s*','§ ',text)
            # Edition's numbered propositions do not represent missing prose.
            text=re.sub(r'(?<!\w)\d+\.\s*','',text)
        text=re.sub(r'\[[^\]]*\]',' § ',text)
        words.extend(lexical_tokens(text));paragraphs+=1
    if not started or not footer or not words:
        raise ValueError('Missing body start or footer anchor')
    return words,{'encoding_used':encoding_used,'body_paragraphs':paragraphs,'barriers':sum(w is None for w in words),
                  'long_words_over_30':sorted(set(w for w in words if w and len(w)>30))}


def load_work(work):
    segments=[];metadata=[];quality=[]
    for filename,url in work['parts']:
        raw,manifest=source(filename)
        if manifest['url']!=url:raise ValueError('Cached source URL mismatch')
        words,audit=extract_html(raw,manifest['encoding'],work['id'],work['start'])
        segments.append(words);metadata.append(manifest);quality.append(audit)
    return segments,metadata,quality


def run(download=False):
    if download:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(fetch,[p for w in WORKS for p in w['parts']]):print(result,flush=True)
    config=json.loads(CONFIG.read_text());validate_inventory(config)
    baseline=json.loads(Path('experiments/results/conflict-selection.json').read_text())
    request=baseline['baseline_request']
    if checksum({'request':request,'codeword_domains':'observed'})!=baseline['baseline_input_sha256']:
        raise ValueError('Baseline hash mismatch')
    if (len(request['ciphertext']['words'])!=22 or sum(map(len,request['ciphertext']['words']))!=104
            or request['bounds']['min_code_length']!=1 or request['bounds']['max_code_length']!=3):
        raise ValueError('Expected fixed 22-word L1–3 baseline')
    rows=[]
    for work in WORKS:
        segments,metadata,quality=load_work(work)
        for profile in ('letters','bounded-seven'):
            rules=[r for r in config['rules'] if r['id'] in config['profiles'][profile]]
            row={'source_id':work['id'],'title':work['title'],'period':work['period'],'genre':work['genre'],
                 'profile':profile,'sources':metadata,'extraction_audit':quality,
                 'records_sha256':checksum(segments),'tokens':sum(w is not None for s in segments for w in s),
                 **diagnose(segments,rules,request['ciphertext']['words'])}
            rows.append(row)
            print(work['id'],profile,'windows',row['windows'],'minimum failures',row['minimum_failed_positions'],
                  'repeat matches',row['repetition_compatible_windows'],flush=True)
    prior_path=Path('experiments/results/latin-length-failures/report.json')
    prior=json.loads(prior_path.read_text())
    if prior['inventory_sha256']!=checksum(config) or prior['baseline_sha256']!=checksum(baseline):
        raise ValueError('Prior analysis has different inventory or ciphertext')
    old=[r for r in prior['rows'] if r['profile']=='bounded-seven' and r['source_id']!='caesar']
    new=[r for r in rows if r['profile']=='bounded-seven']
    summary={'new_windows':sum(r['windows'] for r in new),
             'new_repetition_compatible_windows':sum(r['repetition_compatible_windows'] for r in new),
             'expanded_medieval_windows':sum(r['windows'] for r in old+new),
             'expanded_medieval_repetition_compatible_windows':sum(r['repetition_compatible_windows'] for r in old+new),
             'new_positionwise_length_compatible':sum(r['failed_position_histogram'].get(0,0) for r in new)}
    report={'schema_version':1,'inventory_sha256':checksum(config),'baseline_sha256':checksum(baseline),
            'prior_report_sha256':checksum(prior),'prior_report':str(prior_path),
            'code_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
                           ('benchmarks/expanded_medieval_latin.py','benchmarks/latin_length_failures.py',
                            'benchmarks/latin_contractions.py','benchmarks/historical_word_lengths.py')},
            'work_catalogue':WORKS,'rows':rows,'summary':summary,'complete':True,'solver_calls':0,
            'rejected_sources':[{'url':'https://www.thelatinlibrary.com/albertanus/albertanus1.shtml',
                                 'reason':'Frequent merged words, such as patreluminum and moribusconformare.'},
                                {'url':'https://www.thelatinlibrary.com/abelard/historia.html',
                                 'reason':'Inspected web text has fragmented words around folio markers and stray editorial characters; not downloaded or analyzed.'}],
            'scope':'Four additional edited medieval Latin works; exact prior seven-unit inventory and fixed block. No cross-book/chapter/editorial-gap windows. Ordinary paragraph boundaries may be crossed. Existing historical spelling and u/v,j/i choices retained; no guessed spacing repairs or classicalization. Edited web texts are not diplomatic manuscript orthography. Necessary length/repetition checks, not SMT feasibility or language identification.'}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    with (OUT/'summary.csv').open('w',newline='') as handle:
        columns=['source_id','title','period','profile','tokens','windows','minimum_failed_positions','repetition_compatible_windows']
        writer=csv.DictWriter(handle,fieldnames=columns);writer.writeheader()
        for row in rows:writer.writerow({k:row[k] for k in columns})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',action='store_true')
    args=parser.parse_args();run(args.download)
