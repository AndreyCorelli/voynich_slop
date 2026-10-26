"""Download pinned public UD treebanks; structural metadata only, no label scoring."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import urllib.request

OUT=Path('experiments/datasets/latin-grammar-expansion/v1')
RAW=Path('data/latin-grammar-benchmark')
TAG='r2.17'
CATALOG=[dict(slug='ittb',repo='UD_Latin-ITTB',license='CC-BY-NC-SA-3.0',policy='Aquinas SCG development; mixed-author concordances quarantined',role='development_with_quarantine'),dict(slug='udante',repo='UD_Latin-UDante',license='CC-BY-NC-SA-3.0',policy='All annotation labels reserved; disputed authorship and Giovanni del Virgilio not counted as independent Dante texts',role='reserved_evaluation'),dict(slug='circse',repo='UD_Latin-CIRCSE',license='CC-BY-SA-4.0',policy='Tacitus development; Seneca reserved evaluation; unknown metadata quarantined',role='author_split'),dict(slug='llct',repo='UD_Latin-LLCT',license='CC-BY-SA-4.0',policy='Supplemental development genre; anonymous/multiple scribes, not a single independent author',role='supplemental_development')]

def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'voinich-z3-public-corpus-collector','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=120) as response:return response.read()

def download(c):
    folder=RAW/(c['slug']+'-'+TAG);assert not folder.exists(),folder;folder.mkdir()
    api='https://api.github.com/repos/UniversalDependencies/'+c['repo'];commit=json.loads(fetch(api+'/commits/'+TAG))['sha'];entries=json.loads(fetch(api+'/contents?ref='+commit));files=[e for e in entries if e['type']=='file' and (e['name'].endswith('.conllu') or e['name']=='README.md' or e['name'].upper().startswith('LICENSE'))];assert any(e['name'].endswith('.conllu') for e in files) and any(e['name'].upper().startswith('LICENSE') for e in files)
    record=dict(c,tag=TAG,commit=commit,repository='https://github.com/UniversalDependencies/'+c['repo'],files=[])
    for e in sorted(files,key=lambda e:e['name']):
        name=e['name'];assert '/' not in name and '\\' not in name;url='https://raw.githubusercontent.com/UniversalDependencies/'+c['repo']+'/'+commit+'/'+name;payload=fetch(url);assert hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==e['sha'];path=folder/name;path.write_bytes(payload);record['files'].append(dict(path=str(path),url=url,bytes=len(payload),sha256=sha(path),git_blob_sha1=e['sha']))
    save(OUT/(c['slug']+'-provenance.json'),record);print('downloaded',c['slug'],commit,len(files),flush=True);return record

def main():
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'catalog-freeze.json').exists()
    save(OUT/'catalog-freeze.json',dict(date='2026-10-26',tag=TAG,catalog=CATALOG,collector_sha256=sha(Path(__file__)),scope='Collection only; no inference, models, graph projection, case/POS label distributions or evaluation. Reserve old Ammianus/Quintilian/200-sentence holdout unchanged. New reserve means annotation/model evaluation embargo; older raw-author exposure disclosed separately. Structure/ID counts and headers only may be inventoried; no FORM/text emitted.'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(download,CATALOG))
    save(OUT/'downloads.json',dict(date='2026-10-26',sources=records));print('all downloads complete',flush=True)
if __name__=='__main__':main()
