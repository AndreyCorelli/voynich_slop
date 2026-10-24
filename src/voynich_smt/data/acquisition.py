"""Checksum-verified immutable local imports and catalogued HTTPS acquisition."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from .corpus import write_json

CATALOG = {
    'zl-eva': {'url': 'https://www.voynich.nu/data/ZL3b-n.txt',
               'title': 'Zandbergen–Landini EVA transliteration', 'provider': 'René Zandbergen / Gabriel Landini',
               'version': '3b, 13/05/2025; IVTFF Eva- 2.0', 'filename': 'ZL3b-n.txt',
               'terms_url': 'https://www.voynich.nu/transcr.html',
               'rights': 'No explicit redistribution license established; local research copy only.'},
    'caesar-latin': {'url': 'https://www.gutenberg.org/ebooks/218.txt.utf-8',
                     'title': 'C. Iuli Caesaris De Bello Gallico, I–IV', 'provider': 'Project Gutenberg',
                     'version': 'eBook 218; text header updated 2009-03-15', 'filename': 'pg218.txt',
                     'terms_url': 'https://www.gutenberg.org/ebooks/218',
                     'rights': 'Public-domain classical text; retain original Project Gutenberg terms. Local copy only.'},
}


def acquire(name, root, *, local=None):
    if name not in CATALOG:
        raise ValueError('Unknown corpus source')
    entry = CATALOG[name]
    root = Path(root)
    raw = root / entry['filename']
    manifest = root / (entry['filename'] + '.manifest.json')
    if raw.exists() or manifest.exists():
        if not raw.exists() or not manifest.exists():
            raise ValueError('Incomplete raw artifact; refusing overwrite')
        return read_source(manifest)
    if local is None:
        with urlopen(entry['url'], timeout=45) as response:
            data = response.read(5_000_001)
            final_url = response.geturl()
    else:
        data = Path(local).read_bytes()
        final_url = None  # A local import cannot establish the HTTP redirect chain.
    if len(data) > 5_000_000:
        raise ValueError('Source exceeds five megabytes')
    text = data.decode('utf-8-sig')
    if name == 'zl-eva' and not text.startswith('#=IVTFF Eva- 2.0'):
        raise ValueError('Expected IVTFF EVA 2.0 source')
    if name == 'caesar-latin' and ('*** START OF THE PROJECT GUTENBERG EBOOK' not in text or 'Language: Latin' not in text):
        raise ValueError('Expected Project Gutenberg Latin text')
    root.mkdir(parents=True, exist_ok=True)
    record = {**entry, 'id': name, 'resolved_url': final_url, 'raw_filename': raw.name,
              'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
              'acquisition': 'local import' if local else 'HTTPS download',
              'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'encoding': 'utf-8-sig'}
    with raw.open('xb') as stream:
        stream.write(data)
    write_json(manifest, record)
    return read_source(manifest)


def read_source(manifest):
    manifest = Path(manifest)
    record = json.loads(manifest.read_text(encoding='utf-8'))
    name = record['raw_filename']
    if Path(name).name != name:
        raise ValueError('Raw filename must be local to its manifest')
    data = (manifest.parent / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('Raw source checksum mismatch')
    return record, data.decode(record['encoding'])
