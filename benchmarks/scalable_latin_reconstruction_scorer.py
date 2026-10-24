"""Frozen, bounded discrimination test. Does not change the decoder."""
from collections import Counter
import json
from pathlib import Path
import random
import time

import numpy as np
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.latin_corpus import documents, sha, write
from voynich_smt.word_mapping.scalable.reconstruction_scorer import features, fit_preferences, score

PARENT=Path('experiments/results/scalable-latin-corpus-morphology/v2')
TRIGRAM=Path('experiments/results/scalable-latin-trigram/v1')
SHUFFLE=Path('experiments/results/scalable-latin-shuffle-contrast/v1')
ROOT=Path('experiments/results/scalable-latin-reconstruction-scorer/v1')


def corrupt(words, fraction, seed):
    """Injective type permutation, shared over the complete passage."""
    rng=random.Random(seed); types=sorted(set(words)); selected=rng.sample(types,max(2,int(len(types)*fraction)))
    values=selected.copy();rng.shuffle(values);mapping=dict(zip(selected,values))
    return [mapping.get(w,w) for w in words]


def reconstructed(folder, fixture, inventory):
    inferred=json.loads((folder/'inference.json').read_text())
    from voynich_smt.word_mapping.scalable.data import CipherStream
    stream=CipherStream.load(fixture/'public/cipher.json')
    if inferred['protocol']['cipher_sha256']!=stream.identity:raise ValueError('Cipher mismatch')
    if inferred['protocol']['inventory_sha256']!=inventory.identity:raise ValueError('Inventory mismatch')
    for run in inferred['runs']:
        assignment=run['joint_archive'][0]['assignments']
        mapping={i:inventory.word(w) for i,w in enumerate(assignment)}
        yield run['seed'] if 'seed' in run else run.get('step'), [mapping[c] for c in stream.documents[0]]


def main():
    start=time.monotonic();ROOT.mkdir(parents=True,exist_ok=False)
    design={'source_manifest_sha256':sha(PARENT/'corpus/corpus.json'),
        'training':'Two fixed 256-word windows from up to 6 source files per author; three inspected development works; Apuleius solver negatives',
        'training_authors_excluded_from_test':['Gellius','Livy'],
        'test':['gellius-1','livy-1'],'test_status':'Previously inspected recovery works; no scorer fitting or selection on them',
        'still_sealed':['ammianus-14','quintilian-1'],
        'features':'Signed 65536-bin hashing: lexical unigram, word pairs at distance 1/2, adjacent triples, suffix pairs at 1/2/4/8',
        'models':['unigram control','context plus unigram'], 'L2':1.,'window':256,'maxiter':200,
        'gate':'Both test works: reference above every optimized wrong key, and >=75% correct rankings of unequal-accuracy corruption pairs; necessary diagnostic only',
        'limits':['Source positives overlap base LM training; test authors excluded from both models.',
          'Actual solver training negatives available only for Apuleius; synthetic permutations supplement them.',
          'No morphology tags or target sentences/topics/anchors; suffix contexts are weak learned grammar proxies.',
          'Scores uncalibrated; passing cannot establish search or word-confidence improvement.']}
    write(ROOT/'design.json',design)
    corpus=json.loads((PARENT/'corpus/corpus.json').read_text());records=[];authors=Counter()
    for r in corpus['documents']:
        if authors[r['author']]<6:records.append(r);authors[r['author']]+=1
    pairs=[]
    for index,words in enumerate(documents(PARENT/'corpus',records)):
        for startpoint in (0,max(0,len(words)//2-128)):
            positive=list(words[startpoint:startpoint+256])
            for j,fraction in enumerate((.1,.5,1.)):
                # Corrupt whole source window using a consistent type map.
                pairs.append((positive,corrupt(positive,fraction,10000+index*10+j)))
    inventory=Inventory(PARENT/'models/20000000/surface/inventory.sqlite')
    try:
        for index,name in enumerate(('apuleius-1','curtius-3','suetonius-augustus')):
            words=(PARENT/f'corpus/evaluation-only/{name}.txt').read_text().split()
            negatives=[corrupt(words,f,900+index*10+j) for j,f in enumerate((.1,.5,1.))]
            if name=='apuleius-1':
                for method in ('surface','contrast','regularized'):
                    negatives.extend(seq for _,seq in reconstructed(SHUFFLE/f'smoke-{method}',SHUFFLE/'fixtures'/name,inventory))
            for begin in range(0,len(words)-255,256):
                for negative in negatives:pairs.append((words[begin:begin+256],negative[begin:begin+256]))
        write(ROOT/'training.json',{'source_records':records,'source_authors':dict(authors),'pairs':len(pairs)})
        models={};fits={}
        for context in (False,True):
            differences=[features(a,context=context)-features(b,context=context) for a,b in pairs]
            weights,fit=fit_preferences(differences);label='context' if context else 'unigram'
            np.save(ROOT/f'{label}.npy',weights);models[label]=weights;fits[label]=fit
            print(json.dumps({'stage':'fit','model':label,**fit}),flush=True)
        write(ROOT/'frozen.json',{'models':{k:sha(ROOT/f'{k}.npy') for k in models},'fits':fits})
        # Only now open held-out reference text and optimized test reconstructions.
        rows=[]
        for name,prefix,baseline in [('gellius-1','replication',SHUFFLE/'validation-surface'),('livy-1','confirmation',TRIGRAM/'confirmation-bigram')]:
            words=(PARENT/f'corpus/evaluation-only/{name}.txt').read_text().split();sequences={'reference':words}
            for level in (.1,.25,.5,1.):
                for seed in range(3):sequences[f'corrupt-{level}-{seed}']=corrupt(words,level,88000+seed)
            for method,folder in [('bigram',baseline),('trigram',TRIGRAM/f'{prefix}-trigram')]:
                for i,(_,seq) in enumerate(reconstructed(folder,TRIGRAM/'fixtures'/name,inventory)):
                    sequences[f'{method}-{i}']=seq
            entries={label:{'accuracy':sum(a==b for a,b in zip(words,seq))/len(words),
                         'scores':{m:score(seq,w,context=m=='context') for m,w in models.items()}}
                     for label,seq in sequences.items()}
            checks={}
            for model in models:
                optimized=[e for k,e in entries.items() if k.startswith(('bigram','trigram'))]
                corruptions=[e for k,e in entries.items() if k.startswith('corrupt')]
                comparisons=[(a['scores'][model]>b['scores'][model]) for a in corruptions for b in corruptions if a['accuracy']>b['accuracy']]
                checks[model]={'reference_beats_optimized':sum(entries['reference']['scores'][model]>e['scores'][model] for e in optimized),
                    'optimized_count':len(optimized),
                    'selected_optimized':max((k for k in entries if k.startswith(('bigram','trigram'))),key=lambda k:entries[k]['scores'][model]),
                    'selected_optimized_accuracy':max(optimized,key=lambda e:e['scores'][model])['accuracy'],
                    'best_available_optimized_accuracy':max(e['accuracy'] for e in optimized),
                    'half_correct_beats_optimized':sum(a['scores'][model]>b['scores'][model] for k,a in entries.items() if k.startswith('corrupt-0.5-') for b in optimized),
                    'half_correct_comparisons':3*len(optimized), 'corruption_order_accuracy':sum(comparisons)/len(comparisons),
                    'gate':all(entries['reference']['scores'][model]>e['scores'][model] for e in optimized) and sum(comparisons)/len(comparisons)>=.75}
            rows.append({'work':name,'entries':entries,'checks':checks});write(ROOT/'test-progress.json',rows)
            print(json.dumps({'stage':'test','work':name,'checks':checks}),flush=True)
        write(ROOT/'summary.json',{'works':rows,'fits':fits,'seconds':time.monotonic()-start,
            'context_gate':all(r['checks']['context']['gate'] for r in rows),
            'decoder_changed':False,'sealed_works_opened':False})
    finally:inventory.close()

if __name__=='__main__':main()
