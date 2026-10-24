"""Prepare and fit a lexical-identity-free cipher grammar benchmark."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from benchmarks.scalable_latin_caesar import words,PROIEL
from benchmarks.grammar_relative_constituents_iteration15 import load,save,RESERVE
from voynich_smt.cipher_relations import ARMS,LABELS,RADIUS,DIM,views,candidates,pair_features,masked_number_features,matrix,fit,probabilities,decode
from voynich_smt.relative_constituents import ConstituentAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

ROOT=Path('experiments/results/grammar-restoration');OUT=ROOT/'iteration23'
TREEBANK=Path('data/latin-grammar-benchmark/proiel-r2.17/la_proiel-ud-train.conllu')
THRESHOLDS=(.05,.10,.15,.20,.30,.40,.50,.65,.80)
KEYS={'train':101,'tune':307,'test_jerome':709,'test_caesar':709}
LABEL_MAP={'nsubj':1,'obj':2,'iobj':2,'amod':3,'det':3,'conj':4}


def strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,list):
        for v in value:yield from strings(v)
    elif isinstance(value,dict):
        for v in value.values():yield from strings(v)


def prepare():
    if OUT.exists():raise ValueError('Preserve previous output')
    files=sorted(set(ROOT.rglob('*manifest*.json'))|set(ROOT.rglob('*truth*.json')))
    prior=set().union(*(set(strings(load(p))) for p in files));reserved=set(strings(load(RESERVE)))
    train_ids=set(load(ROOT/'iteration9/manifest.json')['source_split_ids']['train']);fresh={'Jerome':[],'Caesar':[]};train=[]
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        work=next((l.split(' = ',1)[1].split(',')[0] for l in lines if l.startswith('# source = ')),None);author=PROIEL.get(work)
        if sid in reserved:continue  # Skip before parsing any token-level annotation.
        fresh_ok=author in fresh and sid not in prior and len(fresh[author])<(140 if author=='Jerome' else 100)
        if sid not in train_ids and not fresh_ok:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')]
        if any('-' in r[0] for r in rows):continue
        raw={r[0]:r for r in rows if r[0].isdigit()};kept=[r for r in raw.values() if r[3]!='PUNCT'];normalized=[words(r[1]) for r in kept]
        if not 3<=len(kept)<=60 or any(len(w)!=1 for w in normalized):continue
        positions={r[0]:i for i,r in enumerate(kept)}
        def head(index):
            h=raw[index][6];seen=set()
            while h!='0' and h not in positions:
                if h in seen:raise ValueError('Cycle through removed token')
                seen.add(h);h=raw[h][6]
            return positions.get(h)
        edges=[];numbers=[]
        for i,r in enumerate(kept):
            h=head(r[0]);label=LABEL_MAP.get(r[7].split(':')[0]);features=dict(x.split('=',1) for x in r[5].split('|') if '=' in x)
            if h is not None and label is not None:edges.append([i,h,label])
            if features.get('Number') in ('Sing','Plur'):numbers.append([i,int(features['Number']=='Plur')])
        record=dict(sent_id=sid,author=author,tokens=[w[0] for w in normalized],edges=edges,numbers=numbers)
        if sid in train_ids:train.append(record)
        elif fresh_ok:fresh[author].append(record)
    assert len(fresh['Jerome'])==140 and len(fresh['Caesar'])==100
    datasets={'train':train,'tune':fresh['Jerome'][:40],'test_jerome':fresh['Jerome'][40:],'test_caesar':fresh['Caesar']}
    assert all(not ({s['sent_id'] for s in a}&{s['sent_id'] for s in b}) for i,a in enumerate(datasets.values()) for j,b in enumerate(datasets.values()) if i<j)
    assert all(s['sent_id'] not in reserved for ss in datasets.values() for s in ss)
    a=ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'));vocab=sorted({w for ss in datasets.values() for s in ss for w in s['tokens']})
    lattice={w:[asdict(r) for r in a.analyze(w)] for w in vocab}
    OUT.mkdir();save(OUT/'datasets.json',datasets);save(OUT/'morphology-lattice.json',lattice)
    paths=[Path(__file__),Path('src/voynich_smt/cipher_relations.py'),TREEBANK,RESERVE,ROOT/'iteration9/manifest.json']
    save(OUT/'manifest.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},prior_declarations={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        split_ids={split:[s['sent_id'] for s in ss] for split,ss in datasets.items()},
        data_selection='Train: eligible previously declared 800 source training sentences. Fresh tune/test: undeclared eligible Jerome 40/100 and Caesar 100, in source order.',
        eligibility='3..60 nonpunctuation tokens; no multiword token ranges; single normalized word per token.',
        keys=KEYS,test_rekeys=[709,710,711],arms=ARMS,labels=LABELS,radius=RADIUS,dimension=DIM,
        thresholds=THRESHOLDS,regularization=.003,training='Weighted multiclass logistic; no reference predicates/POS/heads supplied to features; sentence boundaries given.',
        ending_blind='Fresh monoalphabetic ending cipher; ending equality/frequency rank only. Full split unlabeled frequency statistics are transductive.',
        ending_exposed='Additional revealed Latin last-two-character ending: explicit oracle upper-bound channel.',
        dictionary='Ambiguous Whitaker POS/case/number/gender/mood/voice supplied before encryption: oracle side channel; no roots/lemmas.',
        auxiliary='Context-only Number prediction at annotated Number-bearing query positions; complete central word type masked; independent auxiliary classifier, not proof that predicted graph explains agreement.',
        lexicon_resource=a.analyzer.resource))
    print('prepared', {k:(len(ss),sum(len(s['tokens']) for s in ss)) for k,ss in datasets.items()},flush=True)


def relation_matrix(sentences,unlabeled,arm):
    features=[];targets=[];slices=[];pairs_by_sentence=[];start=0
    for s,v in zip(sentences,unlabeled):
        pairs=candidates(len(v['tokens']));gold={(c,p):l for c,p,l in s.get('edges',[])}
        features.extend(pair_features(v,c,p,arm) for c,p in pairs);targets.extend(gold.get((c,p),0) for c,p in pairs)
        slices.append((start,start+len(pairs)));pairs_by_sentence.append(pairs);start+=len(pairs)
    return matrix(features),targets,slices,pairs_by_sentence


def number_matrix(sentences,unlabeled,arm):
    features=[];targets=[];queries=[]
    for s,v in zip(sentences,unlabeled):
        for pos,label in s['numbers']:
            features.append(masked_number_features(v,pos,arm));targets.append(label);queries.append([s['sent_id'],pos])
    return matrix(features),targets,queries


def edge_counts(predictions,sentences):
    totals=Counter()
    for pred,s in zip(predictions,sentences):
        guessed={(c,p,l) for c,p,l,confidence in pred};gold=set(map(tuple,s['edges']));totals['tp']+=len(guessed&gold);totals['predicted']+=len(guessed);totals['gold']+=len(gold)
    totals['f1']=2*totals['tp']/max(1,totals['predicted']+totals['gold'])
    return dict(totals)


def run():
    if not OUT.exists():prepare()
    if (OUT/'models.json').exists():raise ValueError('Preserve fitted models')
    data=load(OUT/'datasets.json');lattice=load(OUT/'morphology-lattice.json');models={};tuning={};start=time.monotonic()
    train_views=views(data['train'],KEYS['train'],lattice);tune_views=views(data['tune'],KEYS['tune'],lattice)
    for arm in ARMS:
        x,y,_,_=relation_matrix(data['train'],train_views,arm);model=fit(x,y,len(LABELS))
        tx,_,slices,pairs=relation_matrix(data['tune'],tune_views,arm);p=probabilities(tx,model)
        rows=[]
        for threshold in THRESHOLDS:
            pred=[decode(pair,p[a:b],threshold) for (a,b),pair in zip(slices,pairs)]
            rows.append(dict(threshold=threshold,**edge_counts(pred,data['tune'])))
        best=max(rows,key=lambda r:(r['f1'],r['threshold']))
        nx,ny,_=number_matrix(data['train'],train_views,arm);number=fit(nx,ny,2)
        models[arm]=dict(relation=model,number=number,threshold=best['threshold']);tuning[arm]=rows
        save(OUT/f'checkpoint-{arm}.json',models[arm])
        print(arm,'fit; tune F1',round(best['f1'],4),'threshold',best['threshold'],'elapsed',round(time.monotonic()-start,1),flush=True)
    save(OUT/'models.json',models);save(OUT/'tuning.json',tuning)
    save(OUT/'fit-freeze.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'models.json',OUT/'tuning.json',OUT/'datasets.json',OUT/'morphology-lattice.json',OUT/'manifest.json']},elapsed_seconds=time.monotonic()-start))
    print('All model and threshold choices frozen before fresh test evaluation.',flush=True)

if __name__=='__main__':run()
