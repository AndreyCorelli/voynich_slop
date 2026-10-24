"""Count the downloaded historical comparanda; usage: python SCRIPT RAW_DIRECTORY."""
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
import re, json, hashlib, sys, unicodedata
import xml.etree.ElementTree as ET

root = Path(sys.argv[1])
out = Path(__file__).resolve().parents[1] / 'data/processed/historical-comparanda'
out.mkdir(parents=True, exist_ok=True)

def text(name, selector=None):
    soup = BeautifulSoup((root / (name + '.html')).read_bytes(), 'html.parser')
    return (soup.select_one(selector) if selector else soup).get_text(' ', strip=True)

def between(value, start, end=None):
    value = value[value.index(start):]
    return value[:value.index(end)] if end else value

texts = {
    'emerald-tablet': between(text('emerald', '.mw-parser-output'), 'VERUM SINE MENDACIO'),
    'grosseteste-de-sphaera': between(text('sphaera', '.mw-parser-output'), 'Intentio nostra'),
    'mirror-of-alchemy': between(text('mirror'), 'In many ancient Books', 'Here ends the Mirror'),
    'turba-philosophorum': between(text('turba-latin'), 'TURBA PHILOSOPHORUM IN SECUNDA', 'FINISH.').replace('&', ' et '),
    'manilius-astronomica': '\n'.join(between(text('manilius' + str(i)), start, 'Manilius The Miscellany') for i, start in enumerate(['Carmine divinas', 'Maximus Iliacae', 'In nova', 'Quid tam', 'Hic alius'], 1)),
}
tree = ET.parse(root / 'ptolemy-greek.xml')
namespace = {'t': 'http://www.tei-c.org/ns/1.0'}
body = tree.find('.//t:body', namespace)
assert body is not None
for parent in body.iter():
    for child in list(parent):
        if child.tag.rsplit('}', 1)[-1] == 'note':
            tail = child.tail or ''
            previous = list(parent).index(child) - 1
            if previous >= 0:
                sibling = list(parent)[previous]
                sibling.tail = (sibling.tail or '') + tail
            else:
                parent.text = (parent.text or '') + tail
            parent.remove(child)
texts['ptolemy-tetrabiblos'] = unicodedata.normalize('NFC', ''.join(body.itertext()))
metadata = {
    'emerald-tablet': ('Latin', 'https://la.wikisource.org/wiki/Tabula_Smaragdina'),
    'grosseteste-de-sphaera': ('Latin', 'https://la.wikisource.org/wiki/De_sphaera'),
    'mirror-of-alchemy': ('English', 'https://www.alchemywebsite.com/mirror.html'),
    'turba-philosophorum': ('Latin', 'https://www.alchemy-texts.com/book/turba-philosophorum-extended-edition/'),
    'manilius-astronomica': ('Latin', 'https://www.thelatinlibrary.com/manilius.html'),
    'ptolemy-tetrabiblos': ('Greek', 'https://github.com/PerseusDL/canonical-greekLit/blob/master/data/tlg0363/tlg007/tlg0363.tlg007.perseus-grc2.xml'),
}
results = []
for name, value in texts.items():
    value = re.sub(r'\b\d+[a-z]?\b', '', value)
    words = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*", value.lower())
    counts = Counter(words)
    top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    (out / (name + '.txt')).write_text(value + '\n')
    results.append(dict(id=name, language=metadata[name][0], source=metadata[name][1], tokens=len(words), top10=top, sha256=hashlib.sha256((value + '\n').encode()).hexdigest()))
    print(name, len(words), top)
(out / 'frequencies.json').write_text(json.dumps({'method': 'Lowercase Unicode alphabetic word forms; internal apostrophes retained; no stopword filtering or lemmatization; ties alphabetically; numbers excluded. Chapter headings retained where present. Greek normalized to NFC; accents retained. Latin Turba ampersands expanded to et.', 'texts': results}, indent=2) + '\n')
