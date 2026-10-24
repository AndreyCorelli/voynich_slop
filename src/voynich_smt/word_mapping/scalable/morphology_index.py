"""Compact, resumable ambiguity-preserving inventory analyses."""
from array import array
import json
from pathlib import Path
import sqlite3
import time

import numpy as np

from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from .latin_corpus import sha, write


def alternatives(entries):
    """Semantic analyses, deduplicated independently of stems/duplicate records."""
    result=set()
    for entry in entries:
        for infl in entry['inflections'] or [{'part_of_speech':entry['part_of_speech'],'features':{}}]:
            features=tuple(sorted((k,v) for k,v in infl['features'].items()
                                  if v not in ('X','0')))
            grammar=(infl['part_of_speech'],features,entry['enclitic'])
            result.add((entry['lemma_id'],json.dumps(grammar,separators=(',',':'))))
    return tuple(sorted(result))


class MorphologyIndex:
    def __init__(self,path,inventory):
        self.path=Path(path)
        self.metadata=json.loads((self.path/'metadata.json').read_text())
        if self.metadata['inventory_sha256']!=inventory.identity:
            raise ValueError('Morphology inventory mismatch')
        for name in ('offsets','lemma','grammar'):
            file=self.path/(name+'.npy')
            if sha(file)!=self.metadata['files'][name]:
                raise ValueError('Morphology array changed')
            setattr(self,name,np.load(file,mmap_mode='r'))
        if len(self.offsets)!=inventory.size+1 or self.offsets[-1]!=len(self.lemma) or len(self.lemma)!=len(self.grammar):
            raise ValueError('Morphology dimensions differ')
        self.labels=json.loads((self.path/'labels.json').read_text())
        if digest(self.labels)!=self.metadata['labels_sha256']:
            raise ValueError('Morphology labels changed')
        if 'failures_sha256' in self.metadata and sha(self.path/'failures.json')!=self.metadata['failures_sha256']:
            raise ValueError('Morphology failure audit changed')
        self.identity=digest(self.metadata)

    def analyses(self,word):
        start,end=map(int,self.offsets[word:word+2])
        return tuple((int(l),int(g)) for l,g in zip(self.lemma[start:end],self.grammar[start:end]))

    @classmethod
    def build(cls,path,inventory,vendor,*,batch=10000):
        path=Path(path); path.mkdir(parents=True,exist_ok=True)
        if (path/'metadata.json').exists():
            return cls(path,inventory)
        annotator=WhitakerAnnotator(vendor)
        resource={'inventory_sha256':inventory.identity,'resource':annotator.resource,'format_version':1}
        protocol=path/'protocol.json'
        if protocol.exists():
            if json.loads(protocol.read_text())!=resource:
                raise ValueError('Morphology build inputs changed')
        else: write(protocol,resource)
        db=sqlite3.connect(path/'checkpoint.sqlite')
        db.execute('CREATE TABLE IF NOT EXISTS rows (word INTEGER PRIMARY KEY, analyses TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS failures (word TEXT PRIMARY KEY, reason TEXT NOT NULL)')
        start=db.execute('SELECT coalesce(max(word)+1,0) FROM rows').fetchone()[0]
        t=time.monotonic()
        try:
            buffer=[]
            for wid,word in inventory.connection.execute('SELECT id,word FROM forms WHERE id>=? ORDER BY id',(start,)):
                buffer.append((wid,json.dumps(alternatives(annotator.annotate(word)),separators=(',',':'))))
                if len(buffer)>=batch:
                    db.executemany('INSERT INTO rows VALUES (?,?)',buffer)
                    db.executemany('INSERT OR REPLACE INTO failures VALUES (?,?)',annotator.annotation_failures.items())
                    db.commit(); buffer=[]
                    if wid%100000<batch:
                        print(json.dumps({'stage':'morphology','forms':wid+1,'seconds':time.monotonic()-t}),flush=True)
            db.executemany('INSERT INTO rows VALUES (?,?)',buffer)
            db.executemany('INSERT OR REPLACE INTO failures VALUES (?,?)',annotator.annotation_failures.items())
            db.commit()
            offsets=array('Q',[0]); lemma=array('I'); grammar=array('I'); labels={'lemma':{},'grammar':{}}
            unsupported=0
            for wid,encoded in db.execute('SELECT word,analyses FROM rows ORDER BY word'):
                if wid!=len(offsets)-1: raise ValueError('Noncontiguous morphology checkpoint')
                rows=json.loads(encoded); unsupported+=not bool(rows)
                for l,g in rows:
                    lemma.append(labels['lemma'].setdefault(l,len(labels['lemma'])))
                    grammar.append(labels['grammar'].setdefault(g,len(labels['grammar'])))
                offsets.append(len(lemma))
            files={}
            for name,values in [('offsets',offsets),('lemma',lemma),('grammar',grammar)]:
                np.save(path/(name+'.npy'),np.asarray(values)); files[name]=sha(path/(name+'.npy'))
            write(path/'labels.json',labels)
            write(path/'failures.json',dict(db.execute('SELECT word,reason FROM failures ORDER BY word')))
            write(path/'metadata.json',{**resource,'files':files,'labels_sha256':digest(labels),
                  'forms':inventory.size,'analyses':len(lemma),'unsupported_forms':unsupported,
                  'failures_sha256':sha(path/'failures.json'),
                  'seconds_this_invocation':time.monotonic()-t})
        finally: db.close()
        return cls(path,inventory)
