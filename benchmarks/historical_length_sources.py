"""Fetch immutable local source copies and checksums for historical length analysis."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path('data/raw/historical-lengths')
SOURCES={
 'german-bibliography.html':'https://korpora.org/FnhdC/FnhdC-Bibliographie.html',
 'german-documentation.html':'https://korpora.org/FnhdC/Dokumentation.html',
 'german-download.html':'https://korpora.org/FnhdC/Download.html',
 'czech-dalimil.html':'https://czech.mml.ox.ac.uk/dalimilova-kronika',
 'czech-editorial.html':'https://czech.mml.ox.ac.uk/chrestomatie-editorial-guidelines',
 'czech-bibles.html':'https://czech.mml.ox.ac.uk/vyvoj-jazyka-prekladu-bible',
 'italian-decameron-index.html':'https://it.wikisource.org/wiki/Decameron',
 'german-corpus.tar.xz':'https://korpora.org/FnhdC/Archive/FnhdC.XML.2017.tar.xz',
 'latin-aquinas-ente.html':'https://www.thelatinlibrary.com/aquinas/ente.shtml',
 'latin-alfonsi.html':'https://www.thelatinlibrary.com/alfonsi.disciplina.html',
 'latin-caroli.html':'https://www.thelatinlibrary.com/vitacaroli.html',
}
for ordinal in ('prima','seconda','terza','quarta','quinta','sesta','settima','ottava','nona','decima'):
 SOURCES[f'italian-decameron-1-{ordinal}.html']=f'https://it.wikisource.org/wiki/Decameron/Giornata_prima/Novella_{ordinal}'


def fetch(item):
 name,url=item;path=ROOT/name;manifest=path.with_suffix(path.suffix+'.manifest.json')
 if path.exists():
  if not manifest.exists():raise ValueError('Existing source lacks manifest')
  old=json.loads(manifest.read_text());data=path.read_bytes()
  if hashlib.sha256(data).hexdigest()!=old['sha256']:raise ValueError('Raw checksum mismatch')
  return name,'cached'
 with urlopen(Request(url,headers={'User-Agent':'HistoricalWordLengths/1.0 (local research)'}),timeout=45) as response:
  data=response.read(20000001);resolved=response.geturl();encoding=response.headers.get_content_charset() or 'utf-8'
 if len(data)>20000000:raise ValueError('Source exceeds size bound')
 ROOT.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as out:out.write(data)
 metadata={'url':url,'resolved_url':resolved,'raw_filename':name,'sha256':hashlib.sha256(data).hexdigest(),
   'bytes':len(data),'encoding':encoding,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
   'usage':'Local research only; observe source terms; no redistribution of source text.'}
 manifest.write_text(json.dumps(metadata,indent=2)+'\n')
 return name,len(data)


if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=4) as pool:
  for result in pool.map(fetch,SOURCES.items()):print(result,flush=True)
