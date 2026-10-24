"""Frozen 25-label, preserved-space capacity screen without nulls."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
from benchmarks import currier_mechanism_comparison as base
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.models.text import Text
OUT=Path('experiments/results/currier-alphabet-comparison')
PARENT=base.OUT/'prepared.json'
ARMS=('mono-independent','mono-word-deterministic','allocated-independent','allocated-word-deterministic')

def allocation(alphabet,counts,capacity,homophonic):
    if len(alphabet)>capacity:raise ValueError('Plaintext alphabet exceeds output capacity')
    result={u:1 for u in alphabet}
    if homophonic:
        order=sorted(alphabet,key=lambda u:(-counts[u],u))
        for i in range(capacity-len(alphabet)):result[order[i%len(order)]]+=1
    return result

def key_for(counts,glyphs,seed):
    labels=list(glyphs);random.Random(seed).shuffle(labels);cursor=0;book={}
    for u,n in sorted(counts.items()):book[u]=tuple((g,) for g in labels[cursor:cursor+n]);cursor+=n
    assert cursor<=len(labels)
    return Encoder(book)

def encode(lines,encoder,seed,selection):
    rng=random.Random(seed);out=[]
    for line in lines:
        result=[]
        for word in line:
            glyphs=[]
            for i,u in enumerate(word):
                n=len(encoder.codebook[u])
                key=json.dumps([seed,list(word),i],separators=(',',':'))
                choice=rng.randrange(n) if selection=='independent' else int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%n
                glyphs.extend(encoder.codebook[u][choice])
            result.append(tuple(glyphs))
        out.append(result)
    return out

def prepare():
    parent=json.loads(PARENT.read_text())
    for path,sha in parent['code_sha256'].items():assert digest(Path(path).read_text())==sha
    allocations={};frequencies={}
    for source in parent['sources']:
        alphabet=sorted({u for w in base.natural_stream(parent['sources'][source]) if w for u in w})
        counts=Counter(u for i,t in enumerate(parent['targets']) if t['split']=='development' for w in parent['passages'][source][i]['words'] for u in w)
        frequencies[source]=dict(counts)
        allocations[source]={kind:allocation(alphabet,counts,25,kind=='allocated') for kind in ('mono','allocated')}
    p={'parent_path':str(PARENT),'parent_sha256':digest(parent),'code_sha256':digest(Path(__file__).read_text()),'arms':ARMS,'allocations':allocations,'development_frequencies':frequencies,
       'protocol':'Reuse all parent targets/passages/seeds/metrics;25 existing EVA atomic labels, fixed one-glyph globally distinct codes, preserved spaces only, no nulls or contractions. Mono gives every source character one label; allocated gives every character one label then spare labels to most frequent characters in development passages, lexical ties. Alphabet inventory remains public full source. Independent uniform choice versus SHA256(seed,whole word,letter offset) modulo homophone count. All arms reported, no heldout tuning; German25-letter alphabet has zero spare labels and arms must coincide. Compatibility screen, not key recovery or posterior.'}
    p=json.loads(json.dumps(p));path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p
    else:write_json(path,p)
    return p,parent

def run():
    p,parent=prepare();targets=[base.measure(t['lines']) for t in parent['targets']];summary=[];total=0
    for arm in ARMS:
        kind,selection=arm.split('-',1);rows=[]
        for source in parent['sources']:
            for i,t in enumerate(parent['targets']):
                for seed in parent['seeds']:
                    path=OUT/'cases'/f'{arm}-{source}-{i}-{seed}.json'
                    if path.exists():record=json.loads(path.read_text());assert record['prepared_sha256']==digest(p)
                    else:
                        encoder=key_for(p['allocations'][source][kind],parent['glyphs'],seed)
                        plain=base.layout(parent['passages'][source][i]['words'],list(map(len,t['lines'])))
                        payload=encode(plain,encoder,seed+10,selection)
                        assert encoder.decode(Text(tuple(w for l in payload for w in l)))==Text(tuple(w for l in plain for w in l))
                        m=base.measure(payload);result={'source':source,'target_index':i,'seed':seed,'profile':'preserved','metrics':m,'distances':base.distances(m,targets[i])}
                        record={'prepared_sha256':digest(p),'arm':arm,'source':source,'target_index':i,'seed':seed,'encoder':asdict(encoder),'payload':payload,'result':result};write_json(path,record)
                    rows.append(record['result'])
            print(arm,source,'complete',flush=True)
        summary.extend({'arm':arm,**r} for r in base.summarize(parent,rows));total+=len(rows)
    write_json(OUT/'report.json',{'prepared_sha256':digest(p),'summary':summary,'target_metrics':targets,'cases':total,'complete':True,'solver_calls':0})
    import csv
    fields=['arm','currier','split','source','mean_generated_word_length']+list(summary[0]['distances'])
    with (OUT/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in summary:w.writerow({**{k:r[k] for k in fields[:5]},**{k:v['mean'] for k,v in r['distances'].items()}})

if __name__=='__main__':run()
