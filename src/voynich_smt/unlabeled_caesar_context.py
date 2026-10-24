"""Cached numbered Caesar prose only; deterministic unannotated preprocessing."""
import hashlib
import re
from benchmarks.expanded_medieval_latin import Paragraphs

BOOKS=('gall5','gall6','gall7','bc1','bc2','bc3')


def normalize(word):return word.lower().replace('v','u').replace('j','i')


def letters(text):return ''.join(re.findall('[a-z]+',normalize(text)))


def numbered_prose(raw):
    parser=Paragraphs();parser.feed(raw.decode('utf-8'));parser.close();chapters=[]
    for row in parser.rows:
        if row['classes']:continue
        m=re.match(r'^\s*\[\s*(\d+)\s*\]\s*',row['text'])
        if m:chapters.append((int(m[1]),row['text'][m.end():]))
    if not chapters or [n for n,_ in chapters]!=list(range(1,len(chapters)+1)):raise ValueError('Nonconsecutive Caesar chapters')
    return chapters


def extract(book,raw):
    chapters=numbered_prose(raw);sentences=[]
    for chapter,text in chapters:
        for i,part in enumerate(re.split(r'[.!?]+',text)):
            words=[normalize(w) for w in re.findall(r'[^\W\d_]+',part)]
            if words:sentences.append(dict(sent_id=f'unlabeled104-{book}-{chapter}-{i}',tokens=[dict(word=w) for w in words]))
    return sentences,dict(chapters=len(chapters),raw_sha256=hashlib.sha256(raw).hexdigest(),prose_letters=letters(' '.join(t for _,t in chapters)),sentences=len(sentences),tokens=sum(len(s['tokens']) for s in sentences))


def overlap_fragments(sentences,width=80):
    return {text[i:i+width] for s in sentences for text in [letters(''.join(t['word'] for t in s['tokens']))] for i in range(max(0,len(text)-width+1))}


def overlaps(text,fragments,width=80):
    return any(text[i:i+width] in fragments for i in range(max(0,len(text)-width+1)))
