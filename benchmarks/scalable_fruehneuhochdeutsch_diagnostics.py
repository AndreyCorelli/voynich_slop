"""Evaluation-only scoring controls for frozen historical German trials."""
from collections import Counter
import json
from pathlib import Path
import random

from benchmarks.scalable_fruehneuhochdeutsch_long import ROOT,PARENT
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.latin_corpus import write


def diagnose(inventory,model,name):
    fixture=ROOT/'fixtures'/name;stream=CipherStream.load(fixture/'public/cipher.json')
    truth=json.loads((fixture/'evaluation-only/truth.json').read_text())
    if truth['public_sha256']!=stream.identity:raise ValueError('Truth mismatch')
    known={};missing=[];counts=Counter(stream.documents[0])
    for c,word in enumerate(truth['decoding']):
        try:known[c]=inventory.id(word)
        except KeyError:missing.append(c)
    used=set(known.values());unused=sorted((i for i in range(model.size) if i not in used),key=lambda i:(model.counts[i],i))
    def reference(proxies):
        key=[known.get(c,-1) for c in range(stream.type_count)]
        for c,w in zip(missing,proxies):key[c]=w
        if min(key)<0 or len(set(key))!=len(key):raise ValueError('Infeasible reference')
        return key
    def score(key):return model.score(tuple(key[c] for c in stream.documents[0]))
    key=reference(unused);controls={'reference_rare_proxy':score(key),'reference_common_proxy':score(reference(reversed(unused)))}
    for level in (.1,.25,.5):
        for seed in range(3):
            rng=random.Random(1000+seed);selected=rng.sample(range(stream.type_count),max(2,int(stream.type_count*level)))
            values=[key[c] for c in selected];rng.shuffle(values);candidate=key.copy()
            for c,w in zip(selected,values):candidate[c]=w
            controls[f'corrupt-{level}-{seed}']=score(candidate)
    for seed in range(3):controls[f'random-{seed}']=score(random.Random(seed).sample(range(model.size),stream.type_count))
    optimized=[]
    for method in ('random','frequency'):
        inferred=json.loads((ROOT/'runs'/f'{name}-{method}'/'inference.json').read_text())
        if inferred['protocol']['model_sha256']!=model.identity:raise ValueError('Source model mismatch')
        for run in inferred['runs']:
            entry=run['joint_archive'][0];actual=score(entry['assignments'])
            if abs(actual-entry['score'])>1e-7:raise ValueError('Full-score disagreement')
            optimized.append({'initialization':method,'seed':run['seed'],'score':actual})
    return {'id':name,'covered_reference_token_accuracy':sum(counts[c] for c in known)/sum(counts.values()),
        'missing_types_using_proxies':len(missing),'controls':controls,'optimized':optimized,
        'rare_reference_beats_optimized':sum(controls['reference_rare_proxy']>r['score'] for r in optimized),
        'common_reference_beats_optimized':sum(controls['reference_common_proxy']>r['score'] for r in optimized),
        'optimized_count':len(optimized),
        'note':'References use distinct observed/unobserved inventory proxies for absent true words. They are feasible controls at the inventory coverage ceiling, not solver outputs or full correct keys. Proxies affect contextual scores. No control enters inference.'}


def main():
    rows=[]
    for resources,names in [(PARENT/'resources',('F137','F332','F064')),(ROOT/'long-resources',('arndt-35000',)),(ROOT/'confirmation-resources',('abelin-31260',))]:
        inventory=Inventory(resources/'inventory.sqlite')
        try:
            model=SparseBigram.load(resources/'model.sqlite',inventory)
            for name in names:
                row=diagnose(inventory,model,name);rows.append(row)
                write(ROOT/'objective-diagnostics-progress.json',rows)
                print(json.dumps({'id':name,'reference':row['controls']['reference_rare_proxy'],'reference_beats_optimized':row['rare_reference_beats_optimized']}),flush=True)
        finally:inventory.close()
    write(ROOT/'objective-diagnostics.json',{'works':rows,'evaluation_only':True,'algorithm_changed':False})

if __name__=='__main__':main()
