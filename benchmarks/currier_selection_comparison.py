"""One-glyph H2 capacity diagnostic; independent vs stable word selection."""
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

OUT=Path('experiments/results/currier-selection-comparison')
PARENT=base.OUT/'prepared.json'
SELECTIONS=('independent','word-deterministic')

def key_for(alphabet,seed):
    labels=[f'g{i:02}' for i in range(52)];random.Random(seed).shuffle(labels)
    return Encoder({u:((labels[2*i],),(labels[2*i+1],)) for i,u in enumerate(alphabet)}),tuple(labels[-2:])

def encode(lines,encoder,seed,selection):
    rng=random.Random(seed);result=[];gaps=[]
    for line in lines:
        out=[];offsets=[]
        for word in line:
            emitted=[]
            for i,u in enumerate(word):
                # Stable per word and within-word position; no target fitting.
                key=json.dumps([seed,list(word),i],separators=(',',':'))
                choice=rng.randrange(2) if selection=='independent' else int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%2
                emitted.extend(encoder.codebook[u][choice])
            out.append(tuple(emitted));offsets.append(list(range(len(word)+1)))
        result.append(out);gaps.append(offsets)
    return result,gaps

def prepare():
    parent=json.loads(PARENT.read_text())
    for path,sha in parent['code_sha256'].items():assert digest(Path(path).read_text())==sha
    p={'parent_sha256':digest(parent),'parent_path':str(PARENT),'selections':SELECTIONS,'glyphs':52,
       'code_sha256':digest(Path(__file__).read_text()),'protocol':'Reuse all parent targets, passages, source normalization, seeds, null rates, renewal rules and metrics without selection. H2 fixed one-glyph codewords; globally52 opaque atomic labels, two reserved null labels. Alphabet expansion diagnostic, not a25-label Voynich hypothesis. Independent iid homophone choices versus SHA256(seed,whole plaintext word,within-word offset) modulo2: same plaintext word always emits same payload. Every profile measured separately for A/B and both splits; no parameter tuning, aggregate posterior or classifier.'}
    p=json.loads(json.dumps(p));path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p
    else:write_json(path,p)
    return p,parent

def generate(parent,source,index,seed,selection):
    t=parent['targets'][index];words=parent['passages'][source][index]['words']
    alphabet=sorted({u for w in base.natural_stream(parent['sources'][source]) if w for u in w})
    encoder,nulls=key_for(alphabet,seed);plain=base.layout(words,list(map(len,t['lines'])))
    payload,gaps=encode(plain,encoder,seed+10,selection)
    assert encoder.decode(Text(tuple(w for l in payload for w in l)))==Text(tuple(w for l in plain for w in l))
    profiles={'preserved':payload};budgets={}
    for rate in base.NULL_RATES:
        arms,budget=base.insert_nulls(payload,gaps,nulls,rate,seed+20);budgets[str(rate)]=budget
        for kind,arm in zip(('independent','positional'),arms):profiles[f'{kind}-null-{rate}']=arm
    for expected in base.BOUNDARY_MEANS:profiles[f'renewal-{expected}']=base.resegment(payload,expected,seed+30)
    return {'source':source,'target_index':index,'seed':seed,'selection':selection,'encoder':asdict(encoder),'null_glyphs':nulls,'payload':payload,'budgets':budgets,'profiles':profiles}

def run():
    p,parent=prepare();target_metrics=[base.measure(t['lines']) for t in parent['targets']];summaries=[];total=0
    for selection in SELECTIONS:
        rows=[]
        for source in parent['sources']:
            for i,t in enumerate(parent['targets']):
                for seed in parent['seeds']:
                    path=OUT/'cases'/f'{selection}-{source}-{i}-{seed}.json'
                    if path.exists():record=json.loads(path.read_text());assert record['prepared_sha256']==digest(p)
                    else:
                        g=generate(parent,source,i,seed,selection);results=[]
                        for profile,lines in g['profiles'].items():
                            m=base.measure(lines);results.append({'source':source,'target_index':i,'seed':seed,'profile':profile,'metrics':m,'distances':base.distances(m,target_metrics[i])})
                        record={'prepared_sha256':digest(p),'generation':g,'results':results};write_json(path,record)
                    rows+=record['results']
                print(selection,source,'packet',i+1,'/24',flush=True)
        summaries.extend({'selection':selection,**s} for s in base.summarize(parent,rows));total+=len(rows)
    write_json(OUT/'report.json',{'prepared_sha256':digest(p),'target_metrics':target_metrics,'summary':summaries,'paired_payloads':432,'generated_metric_cases':total,'complete':True,'solver_calls':0})
    import csv
    fields=['selection','currier','split','source','profile','mean_generated_word_count','mean_generated_word_length']+list(summaries[0]['distances'])
    with (OUT/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for s in summaries:w.writerow({**{k:s[k] for k in fields[:7]},**{k:v['mean'] for k,v in s['distances'].items()}})

if __name__=='__main__':run()
