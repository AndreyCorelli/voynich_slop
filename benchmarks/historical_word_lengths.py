"""Offline historical 22-word length distributions; no solver imports or calls."""
from collections import Counter, deque
import csv
import hashlib
import json
from pathlib import Path
import re
import tarfile
import unicodedata as U
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

ROOT=Path('data/raw/historical-lengths')
OUT=Path('experiments/results/historical-word-lengths')
WINDOW=22
CEILING_TOTAL=104
GERMAN_IDS=(113,123,133,143,153,223,233,243,253)
SUPERSCRIPT={'\u0363':'a','\u0364':'e','\u0365':'i','\u0366':'o','\u0367':'u',
             '\u036c':'r','\u1de0':'n','\u036e':'v','\u033e':'s','\u031a':'ri'}
LIGATURES=str.maketrans({'ſ':'s','æ':'ae','œ':'oe','ﬀ':'ff','ﬁ':'fi','ﬂ':'fl','ﬃ':'ffi','ﬄ':'ffl'})
ABBREVIATION_MARKS={'\u0305','\u0304','\u0309'}


def checksum(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def source(name):
    path=ROOT/name;manifest=json.loads(path.with_suffix(path.suffix+'.manifest.json').read_text())
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['sha256']:raise ValueError(f'Checksum mismatch: {name}')
    return raw,manifest


def letters(word,german=False,graphemic=False):
    word=word.lower().translate(LIGATURES)
    if german:
        word=word.replace('ß','ß' if graphemic else 'ss')
        # These are graphical umlaut variants, not additional full-size vowels.
        word=re.sub('([aou])\u0364',lambda m:m.group(1)+'\u0308',word)
        if not graphemic:word=word.replace('`','er').replace("'",'us')
    result=[]
    for char in U.normalize('NFD',word):
        if char in SUPERSCRIPT:
            if not graphemic:result.append(SUPERSCRIPT[char])
        elif char.isalpha():result.append(char)
        # Accents, umlaut marks and quantity marks do not add letters.
    return ''.join(result)


def lexical_tokens(text,apostrophe_split=False,german=False,graphemic=False,exclude_unresolved=False):
    """None is a barrier, never a zero-length word or a silently omitted word."""
    text=U.normalize('NFC',text).replace('’',"'").replace('‘',"'")
    for chunk in re.split(r'[\s,.;:!?—–“”«»(){}\[\]/]+',text):
        if not chunk:continue
        if chunk=='§' or any(c.isdigit() for c in chunk):yield None;continue
        if exclude_unresolved and any(c in ABBREVIATION_MARKS for c in U.normalize('NFD',chunk)):
            yield None;continue
        for part in re.split(r"[-']" if apostrophe_split else r'[-]',chunk):
            normalized=letters(part,german,graphemic)
            if normalized:yield normalized


def distribution(segments):
    histogram=Counter();tokens=0;barriers=0;nonoverlap=Counter()
    for segment in segments:
        queue=deque();total=0;block=[]
        for word in segment:
            if word is None:
                queue.clear();total=0;block=[];barriers+=1;continue
            n=len(word);tokens+=1;queue.append(n);total+=n;block.append(n)
            if len(queue)>WINDOW:total-=queue.popleft()
            if len(queue)==WINDOW:histogram[total]+=1
            if len(block)==WINDOW:nonoverlap[sum(block)]+=1;block=[]
    def summarize(h):
        count=sum(h.values())
        if not count:return {'windows':0}
        values=sorted(h)
        def rank_value(rank):
            seen=0
            for value in values:
                seen+=h[value]
                if rank<seen:return value/WINDOW
        def quantile(p):
            pos=(count-1)*p;low=int(pos);high=low if low==pos else low+1
            return rank_value(low)+(rank_value(high)-rank_value(low))*(pos-low)
        return {'windows':count,'minimum':values[0]/WINDOW,'p01':quantile(.01),
                'p05':quantile(.05),'p25':quantile(.25),'median':quantile(.5),
                'p75':quantile(.75),'p95':quantile(.95),'p99':quantile(.99),
                'maximum':values[-1]/WINDOW,'mean_of_window_means':sum(k*v for k,v in h.items())/(WINDOW*count),
                'windows_at_or_below_ceiling':sum(v for k,v in h.items() if k<=CEILING_TOTAL),
                'fraction_at_or_below_ceiling':sum(v for k,v in h.items() if k<=CEILING_TOTAL)/count,
                'histogram_total_letters':dict(sorted(h.items()))}
    return {'tokens':tokens,'barriers':barriers,**summarize(histogram),'nonoverlapping':summarize(nonoverlap)}


def html_text(node):
    clone=BeautifulSoup(str(node),'html.parser')
    for tag in clone.select('script,style,sup,.pagenum,.ws-noexport,.noprint,.reference,.mw-editsection'):
        tag.decompose()
    for tag in clone.find_all('br'):tag.replace_with('\n')
    return clone.get_text('',strip=False)


def latin_segments(name,incipit):
    raw,metadata=source(name);soup=BeautifulSoup(raw.decode(metadata['encoding']),'html.parser')
    text=soup.get_text('\n')
    start=text.index(incipit)
    tail=text[start:]
    ends=[m.start() for m in re.finditer(r'(?:St\. Thomas Aquinas|Medieval Latin|Christian Latin|The Latin Library)',tail)]
    if not ends:raise ValueError('Latin footer not found')
    tail=tail[:min(ends)]
    # Editorial chapter numbers/headings are not vocabulary tokens.
    tail=re.sub(r'(?m)^\s*(?:\[[IVX]+\]\.?|Capitulum [IVX]+\.|CONCLUSIO:)\s*$', '§',tail)
    tail=re.sub(r'\[[^\]]+\]',lambda m:m.group()[1:-1],tail)
    return [list(lexical_tokens(tail))],metadata


def italian_segments(apostrophe_split=False):
    segments=[];metadata=[]
    for ordinal in ('prima','seconda','terza','quarta','quinta','sesta','settima','ottava','nona','decima'):
        name=f'italian-decameron-1-{ordinal}.html';raw,meta=source(name)
        soup=BeautifulSoup(raw.decode(meta['encoding']),'html.parser')
        main=soup.select_one('#box_esterno.testi')
        if main is None:raise ValueError('Italian text container missing')
        paragraphs=main.find_all('p')
        if len(paragraphs)<3:raise ValueError('Italian prose extraction unexpectedly short')
        # Remove the opening novella rubric; retain only narration/dialogue.
        text='\n'.join(html_text(p) for p in paragraphs
                       if not p.find_parent(class_='centertext') and not p.find_parent(class_='indent'))
        text=re.sub(r'\[[IVX]+\]','',text)
        segments.append(list(lexical_tokens(text,apostrophe_split=apostrophe_split)))
        metadata.append(meta)
    return segments,metadata


def czech_segments(column='transcription',suppress_expansions=False):
    raw,meta=source('czech-dalimil.html');soup=BeautifulSoup(raw.decode(meta['encoding']),'html.parser')
    selector='.field--name-field-text-2' if column=='transcription' else '.field--name-field-text-1'
    node=soup.select_one(selector)
    if node is None:raise ValueError('Parallel Czech column missing')
    segments=[];pending=[]
    for paragraph in node.find_all('p'):
        if paragraph.get_text().strip().startswith('Source:'):break
        clone=BeautifulSoup(str(paragraph),'html.parser')
        for heading in clone.find_all('strong'):
            if heading.get_text().startswith('[f.'):
                heading.unwrap()  # Some folio labels straddle a bold tag.
            else:
                heading.replace_with(' § ')
        text=html_text(clone)
        text=re.sub(r'\[f\.[^\]]+\]','',text)
        text=re.sub(r'(?m)^\s*\([ivx]+\)\s*','',text)
        text=re.sub(r'<([^<>]+)>',lambda m:'' if suppress_expansions else m.group(1),text)
        text=re.sub(r'\[([^\]]+)\]',lambda m:m.group(1),text)
        text=re.sub(r'(?m)^\s*-\s*$', '§',text)
        pending.extend(lexical_tokens(text))
    if pending:segments.append(pending)
    return segments,meta


def german_sources(graphemic=False,exclude_unresolved=True):
    raw,archive_meta=source('german-corpus.tar.xz');del raw
    entries=[]
    with tarfile.open(ROOT/'german-corpus.tar.xz') as archive:
        for number in GERMAN_IDS:
            data=archive.extractfile(f'XML/{number}.xml').read();root=ET.fromstring(data)
            bib=root.find('bibliographie');base=bib.find('Basis')
            metadata={'archive':archive_meta,'xml_member':f'XML/{number}.xml',
                'xml_sha256':hashlib.sha256(data).hexdigest(),'title':base.findtext('Titel'),
                'short_title':' '.join(base.find('Kurztitel').itertext()),
                'region':base.findtext('Landschaft/Sprachraum'),'date':base.findtext('Zeit/Jahr'),
                'period':base.findtext('Zeit/philnr'),'genre':bib.findtext('Zusatz/Textart')}
            if metadata['period']!='III':raise ValueError('German source not in fifteenth-century bin')
            words=[];unresolved=0;forms=0
            def walk(node):
                nonlocal unresolved,forms
                if node.tag in {'bibliographie','annotation'}:return
                if node.tag in {'eingriff','ueberschrift'}:
                    words.append(None);return
                if node.tag=='wortform':
                    # Distinct morph children encode actual separate written words.
                    for morph in node.findall('morph'):
                        value=''.join(morph.itertext());forms+=1
                        if any(c in ABBREVIATION_MARKS for c in U.normalize('NFD',value)):unresolved+=1
                        words.extend(lexical_tokens(value,german=True,graphemic=graphemic,
                                                    exclude_unresolved=exclude_unresolved))
                    return
                for child in node:walk(child)
            walk(root)
            metadata['morph_forms_seen']=forms;metadata['unresolved_abbreviation_forms']=unresolved
            entries.append((f'german-{number}',[words],metadata))
    return entries


def czech_bible_segments():
    raw,meta=source('czech-bibles.html');soup=BeautifulSoup(raw.decode(meta['encoding']),'html.parser')
    body=soup.select_one('.field--name-body')
    entries=[]
    for heading in body.find_all('h3')[:4]:
        words=[]
        for node in heading.next_siblings:
            if getattr(node,'name',None)=='h3':break
            if getattr(node,'name',None)!='p':continue
            if node.get_text().strip().startswith(('[','Source:')):continue
            text=html_text(node)
            text=re.sub(r'<([^<>]+)>',lambda m:m.group(1),text)
            words.extend(lexical_tokens(text))
        entries.append((heading.get_text(),[words],meta))
    if len(entries)!=4:raise ValueError('Expected four fifteenth-century Czech prose versions')
    return entries


def caesar_segments():
    path=Path('data/processed/caesar-latin-v2.json');data=json.loads(path.read_text())
    if data['normalization']['parser_version']!=2:raise ValueError('Corrected Caesar corpus required')
    words=[''.join(r['tokens']) if r['tokens'] else None for r in data['records']]
    return [words],{'corpus':str(path),'corpus_sha256':checksum(data),'source':data['source'],
                    'normalization':data['normalization']}


def run():
    OUT.mkdir(parents=True,exist_ok=True);rows=[]
    def add(identifier,group,segments,metadata,normalization,primary=True):
        row={'id':identifier,'group':group,'primary':primary,'sources':metadata,
             'normalization':normalization,**distribution(segments)}
        if not row['windows']:raise ValueError(f'No complete windows: {identifier}')
        rows.append(row);return row
    seg,meta=caesar_segments();add('caesar','Caesar',seg,[meta],'Preserved corrected v2 normalization; j→i, u/v preserved, diacritics removed; excluded records break runs.')
    latin_all=[];latin_meta=[]
    for name,incipit,title in [('latin-aquinas-ente.html','Quia parvus error','Aquinas: De ente et essentia (13th c.)'),
                               ('latin-caroli.html','Secundis sedentibus','Vita Caroli IV (14th c.)')]:
        seg,meta=latin_segments(name,incipit);meta['title']=title;latin_all.extend(seg);latin_meta.append(meta)
        add(name[:-5],'Medieval Latin',seg,[meta],'Historical spellings retained; no que→quae/nichil→nihil classicalization; ligatures expanded; headings/numbers excluded.',False)
    add('medieval-latin','Medieval Latin',latin_all,latin_meta,'Pooled two edited medieval prose works; no cross-work/chapter/number windows; full words, historical spelling, ligatures expanded.')
    german=german_sources();pooled=[];metas=[]
    for identifier,seg,meta in german:
        pooled.extend(seg);metas.append(meta)
        add(identifier,'15th-c. German',seg,[meta],'Source-separated morph boundaries; ß→ss, a/o/u with superscript e→umlaut (one letter), other superscript letters expanded; known `→er / apostrophe→us abbreviations expanded; unresolved abbreviations and editorial insertions break windows.',False)
    add('german','15th-c. German',pooled,metas,'Nine period-III varieties; source word divisions; historical spelling with graphical umlaut variants unified and known abbreviation expansions; exclude windows touching unresolved abbreviations/editorial insertions.')
    for identifier,graphemic in [('german-abbreviations-written',False),('german-graphemic',True)]:
        sources=german_sources(graphemic=graphemic,exclude_unresolved=False)
        add(identifier,'15th-c. German',[seg for _,segments,_ in sources for seg in segments],
            [m for _,_,m in sources],
            'Sensitivity: unresolved abbreviation-bearing forms included as written; '+
            ('base graphemes only, ß one unit, superscripts not additional letters; no abbreviation expansion.' if graphemic else 'same letter expansions as primary; unresolved nasal marks do not supply invented letters.'),False)
    seg,meta=italian_segments();add('italian','Medieval Italian',seg,meta,'Decameron day 1, ten separate stories; historical forms in Massera 1927 edition; internal apostrophes retained in one written word; accents one letter, no elision expansion.')
    seg,meta=italian_segments(True);add('italian-apostrophe-split','Medieval Italian',seg,meta,'Sensitivity: internal apostrophes split into separate tokens; no missing letters invented.',False)
    for column in ('transcription','diplomatic'):
        seg,meta=czech_segments(column)
        add('czech-'+column,'Old Czech',seg,[meta],
            'Dalimil parallel '+column+' column; historical language, ch/cz/ss digraphs retain written length, long-s→s, diacritics one base letter; folio labels/headings removed; scribal expansions retained; gaps break windows.',column=='diplomatic')
    seg,meta=czech_segments('diplomatic',True);add('czech-abbreviated','Old Czech',seg,[meta],
        'Sensitivity: diplomatic column with explicitly bracketed scribal expansion letters suppressed; conservative as-written estimate, not reconstruction of manuscript glyphs.',False)
    for index,(title,seg,meta) in enumerate(czech_bible_segments(),1):
        add(f'czech-bible-{index}','Old Czech',seg,[{**meta,'text_version':title}],
            'Fifteenth-century Genesis 22:1–14 prose excerpt; historical spelling preserved, scribal expansions retained, long-s normalized, diacritics one base letter; verse numbers and manuscript references excluded.',False)
    report={'schema_version':1,'normalization_version':1,
            'analysis_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'window_words':WINDOW,'ceiling_total_letters':CEILING_TOTAL,
            'ceiling_mean':CEILING_TOTAL/WINDOW,'primary_order':['caesar','medieval-latin','german','italian','czech-diplomatic'],
            'method':'All overlapping complete windows within uninterrupted runs; exact integer total<=104. Pooled by window count, also individual German/Latin rows and disjoint-window sensitivity. No solver imports or calls.',
            'limitations':['Selected editions/genres are not representative random samples of languages.',
              'Edited word boundaries and expanded abbreviations are not necessarily manuscript glyph counts.',
              'German primary excludes unresolved abbreviation-bearing windows, which may cause selection bias; as-written sensitivities supplied.',
              'Dalimil is a small verse sample; parallel columns are different critical versions, not a pure orthography-only intervention.',
              'Alfonsi Disciplina source rejected for visible missing interword spaces.',
              'Fractions are empirical passage proportions, not posterior language probabilities or sufficient cipher fits.'],
            'rows':rows,'complete':True}
    (OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    with (OUT/'summary.csv').open('w',newline='') as f:
        fields=['id','group','primary','tokens','windows','minimum','p05','median','p95','maximum','fraction_at_or_below_ceiling']
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    with (OUT/'distributions.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['id','total_letters','mean_letters','window_count','cumulative_fraction'])
        for row in rows:
            cumulative=0
            for total,count in row['histogram_total_letters'].items():
                cumulative+=count;writer.writerow([row['id'],total,total/WINDOW,count,cumulative/row['windows']])
    plot(report)
    for r in rows:
        print(f"{r['id']:30} words={r['tokens']:7} windows={r['windows']:7} p05={r['p05']:.2f} median={r['median']:.2f} p95={r['p95']:.2f} ceiling={100*r['fraction_at_or_below_ceiling']:.2f}%")
    return report


def plot(report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    for identifier in report['primary_order']:
        row=next(r for r in report['rows'] if r['id']==identifier)
        counts=row['histogram_total_letters'];xs=[];ys=[];seen=0
        for total,count in counts.items():
            seen+=count;xs.append(total/WINDOW);ys.append(seen/row['windows']*100)
        ax.step(xs,ys,where='post',linewidth=2,label=f"{row['group']} ({100*row['fraction_at_or_below_ceiling']:.1f}% ≤ ceiling)")
    ax.axvline(104/22,color='black',linestyle='--',linewidth=1.5,label='Voynich ceiling: 104/22 = 4.727')
    ax.set(xlabel='Mean letters per word in a 22-word window',ylabel='Percentage of windows at or below this mean',
           title='Historical text samples: 22-word-window length distributions',ylim=(0,100),xlim=(2.5,9))
    ax.grid(alpha=.2);ax.legend(loc='lower right',fontsize=9)
    for suffix in ('svg','png','pdf'):fig.savefig(OUT/f'window-length-cdf.{suffix}',dpi=170)
    plt.close(fig)


if __name__=='__main__':run()
