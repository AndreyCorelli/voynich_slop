"""Unforced Voynich word-map probe with frozen historical German resources."""
import argparse
from collections import Counter,defaultdict
from dataclasses import replace
import json
from pathlib import Path
import random

from voynich_smt.data.corpus import Corpus
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.latin_corpus import sha,write

SOURCE=Path('data/processed/zl-eva.json')
RESOURCES=Path('experiments/results/scalable-fruehneuhochdeutsch/v1/resources')
REFERENCE=Path('experiments/results/scalable-english/independent-wells-frequency-8000-v2/protocol.json')
ROOT=Path('experiments/results/scalable-voynich-fruehneuhochdeutsch/v1')


def segments(records):
    """No invented adjacency across excluded words/folios; lines are not sentences."""
    docs=[];locations=[];current=[];loc=[];previous=None
    def flush():
        if current:docs.append(tuple(current));locations.append(tuple(loc));current.clear();loc.clear()
    seen=set()
    for r in records:
        key=(r['folio'],r['locus'],r['word_in_locus'])
        if key in seen:raise ValueError('Multiple transcription versions at one position')
        seen.add(key)
        if previous is not None and previous!=r['folio']:flush()
        previous=r['folio']
        if r['excluded_reason'] or not r['tokens']:
            flush();continue
        if ''.join(r['tokens'])!=r['raw'] or not r['raw'].isalpha() or not r['raw'].isascii():raise ValueError('Unexpected basic EVA surface')
        current.append(r['raw']);loc.append({'folio':r['folio'],'locus':r['locus'],'word_in_locus':r['word_in_locus']})
    flush();return tuple(docs),tuple(locations)


def split_at(docs,cut):
    left=[];right=[];count=0
    for doc in docs:
        n=max(0,min(len(doc),cut-count))
        if n:left.append(doc[:n])
        if n<len(doc):right.append(doc[n:])
        count+=len(doc)
    return tuple(left),tuple(right)


def shuffled(stream,seed):
    rng=random.Random(seed);docs=[]
    for original in stream.documents:
        doc=list(original);middle=doc[1:-1];rng.shuffle(middle);doc[1:-1]=middle;docs.append(tuple(doc))
    return CipherStream(tuple(docs),stream.type_count,tokenization=stream.tokenization)


def prepare():
    ROOT.mkdir(parents=True,exist_ok=False);corpus=Corpus.load(SOURCE);docs,locations=segments(corpus.records)
    if not docs:raise ValueError('No clean source words')
    vocab=sorted({w for doc in docs for w in doc});random.Random(83).shuffle(vocab);ids={w:i for i,w in enumerate(vocab)}
    model=json.loads((RESOURCES/'report.json').read_text())
    design={'source_sha256':sha(SOURCE),'source':corpus.source,'source_normalization':corpus.normalization,
        'resources':str(RESOURCES),'model_sha256':model['model_sha256'],'inventory_sha256':model['inventory_sha256'],
        'reference_sha256':sha(REFERENCE),'reference_protocol':json.loads(REFERENCE.read_text()),
        'hypothesis':'Historical German and an injective word-substitution channel; neither is established for Voynich.',
        'constraint':'No preferred word, seeded translation, supplied anchors, EVA spelling/length matching, inferred sentences, topic or section-selected language model.',
        'starts':'Random only, seeds3/5/7; 8000 proposals; mixed scheduler and original English numeric settings; runtime allowance1200 per chain',
        'source_policy':'Use all retained basic-EVA words, existing uncertain-space split policy; excluded words and folio changes are barriers, physical lines are not sentence resets.',
        'contract_tag':'CipherStream tokenization is the frozen model compatibility tag; actual source segmentation/notation remains EVA and is never interpreted as German characters.',
        'control':'One endpoint-preserving per-segment interior shuffle, seed2701, same exact vocabulary/counts/endpoints/segment lengths and paired random initial keys.',
        'sections':'First and second equal-token manuscript halves by position, no Currier/topic/language selection; independent runs with dense opaque ID remapping.',
        'ranking':'Inspect all most-voted mappings; primary unanimous three runs with public count>=100; top50 agreement then count then opaque ID. No targeted word search enters inference.',
        'evaluation':'No plaintext truth or recovery accuracy exists. Agreement, section replication and shuffle controls are diagnostics, not calibrated translation probabilities.',
        'preservation':'Versioned local research artifacts; original transcription rights statement retained.'}
    write(ROOT/'design.json',design);total=sum(map(len,docs));left,right=split_at(docs,total//2)
    fixtures={}
    for name,words in [('actual',docs),('first-half',left),('second-half',right)]:
        observed=sorted({ids[w] for doc in words for w in doc});dense={c:i for i,c in enumerate(observed)}
        stream=CipherStream(tuple(tuple(dense[ids[w]] for w in doc) for doc in words),len(observed),tokenization=model['tokenization'])
        stream.save(ROOT/'fixtures'/name/'public/cipher.json')
        write(ROOT/'fixtures'/name/'inspection-only/type-map.json',{'cipher_to_eva':[vocab[c] for c in observed]})
        fixtures[name]={'tokens':sum(map(len,words)),'types':stream.type_count,'segments':len(words),'cipher_sha256':stream.identity}
        if name=='actual':
            control=shuffled(stream,2701);control.save(ROOT/'fixtures/shuffled/public/cipher.json')
            write(ROOT/'fixtures/shuffled/inspection-only/type-map.json',{'cipher_to_eva':[vocab[c] for c in observed]})
            assert Counter(c for d in stream.documents for c in d)==Counter(c for d in control.documents for c in d)
            assert all((a[0],a[-1],len(a))==(b[0],b[-1],len(b)) for a,b in zip(stream.documents,control.documents))
            fixtures['shuffled']={'tokens':total,'types':stream.type_count,'segments':len(words),'cipher_sha256':control.identity,
                'positions_changed':sum(a!=b for da,db in zip(stream.documents,control.documents) for a,b in zip(da,db))}
    write(ROOT/'inspection-only/positions.json',locations)
    write(ROOT/'preparation.json',{'fixtures':fixtures,'folios':len({r['folio'] for r in corpus.records}),'excluded_word_records':len(corpus.records)-total,
        'global_vocabulary_sha256':sha(ROOT/'fixtures/actual/inspection-only/type-map.json')})
    print(json.dumps(fixtures),flush=True)


def trial(name):
    from benchmarks.scalable_english_run import run
    from voynich_smt.word_mapping.scalable.search import SearchConfig
    from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
    design=json.loads((ROOT/'design.json').read_text());protocol=design['reference_protocol']
    if sha(SOURCE)!=design['source_sha256'] or sha(REFERENCE)!=design['reference_sha256']:raise ValueError('Frozen inputs changed')
    resource=json.loads((RESOURCES/'report.json').read_text())
    if resource['model_sha256']!=design['model_sha256']:raise ValueError('Model changed')
    cfg=replace(SearchConfig(**protocol['search']),initialization='random',proposals=8000,budget_seconds=1200)
    run(RESOURCES,ROOT/'fixtures'/name/'public/cipher.json',ROOT/'runs'/name,seeds=(3,5,7),config=cfg,retrieval=RetrievalConfig(**protocol['retrieval']),trace=True)
    inspect(name)


def inspect(name):
    from voynich_smt.word_mapping.scalable.trigram import load_model
    from voynich_smt.word_mapping.scalable.incremental import full_score
    from voynich_smt.word_mapping.scalable.state import DictionaryState
    from voynich_smt.word_mapping.scalable.search import DictionarySearch
    from voynich_smt.word_mapping.scalable.confidence import extract
    output=ROOT/'runs'/name;inference=json.loads((output/'inference.json').read_text());stream=CipherStream.load(output/'public/cipher.json')
    write(output/'confidence-public.json',extract(RESOURCES,output))
    types=json.loads((ROOT/'fixtures'/name/'inspection-only/type-map.json').read_text())['cipher_to_eva'];counts=Counter(c for d in stream.documents for c in d)
    inv=Inventory(RESOURCES/'inventory.sqlite')
    try:
        model=load_model(RESOURCES/'model.sqlite',inv);keys=[];validated=0
        if inference['protocol']['cipher_sha256']!=stream.identity or inference['protocol']['model_sha256']!=model.identity:raise ValueError('Inference binding mismatch')
        for result in inference['runs']:
            checkpoint=DictionarySearch.load(output/f"seed-{result['seed']}/checkpoint.json",model,stream)
            if abs(full_score(model,stream,checkpoint.scorer.state)-result['current_score'])>1e-7:raise ValueError('Current-score mismatch')
            initial=DictionaryState.initialize(stream,model,method='random',seed=result['seed'])
            if abs(full_score(model,stream,initial)-result['initial_score'])>1e-7:raise ValueError('Initial-score mismatch')
            for entry in result['joint_archive']:
                state=DictionaryState.create(stream,model,entry['assignments'])
                if abs(full_score(model,stream,state)-entry['score'])>1e-7:raise ValueError('Archived-score mismatch')
                validated+=1
            keys.append(result['joint_archive'][0]['assignments'])
        rows=[]
        for c in counts:
            votes=Counter(k[c] for k in keys);word,n=min(votes.items(),key=lambda p:(-p[1],p[0]))
            rows.append({'cipher':c,'eva':types[c],'count':counts[c],'votes':n,'prediction':inv.word(word),
                'per_seed':{str(r['seed']):inv.word(k[c]) for r,k in zip(inference['runs'],keys)}})
        rows.sort(key=lambda r:(-r['votes'],-r['count'],r['cipher']))
        primary=[r for r in rows if r['votes']==3 and r['count']>=100]
        report={'name':name,'tokens':sum(counts.values()),'types':stream.type_count,'segments':len(stream.documents),
            'primary':primary,'top50':rows[:50],'all_predictions':rows,'validated_archive_keys':validated,
            'chains':[{'seed':r['seed'],'step':r['step'],'stop_reason':r['stop_reason'],'score':r['best_score'],'seconds':r['elapsed_seconds']} for r in inference['runs']],
            'selected_seed':inference['selected_seed'],'accuracy':'unknown','confidence':'uncalibrated; shared model bias can produce unanimous errors'}
        write(output/'inspection.json',report)
        selected=next(r for r in inference['runs'] if r['seed']==inference['selected_seed'])['joint_archive'][0]['assignments']
        for offset in (0,1000,10000):
            flat=[c for d in stream.documents for c in d];part=flat[offset:offset+100]
            (output/f'excerpt-{offset}.md').write_text('# Exploratory word-map output, not a translation\n\nEVA:\n\n'+' '.join(types[c] for c in part)+'\n\nModel guesses:\n\n'+' '.join(inv.word(selected[c]) for c in part)+'\n')
        print(json.dumps({'stage':'inspected','name':name,'primary':primary}),flush=True)
    finally:inv.close()


def summarize():
    reports={name:json.loads((ROOT/'runs'/name/'inspection.json').read_text()) for name in ('actual','shuffled','first-half','second-half')}
    for report in reports.values():
        if any(c['step']!=8000 or c['stop_reason']!='proposal_limit' for c in report['chains']):raise ValueError('Incomplete trial; report unequal caps explicitly')
    mapped={name:{r['eva']:r for r in report['all_predictions']} for name,report in reports.items()}
    candidates=[]
    for row in reports['actual']['primary']:
        checks={name:{'prediction':mapped[name][row['eva']]['prediction'],'votes':mapped[name][row['eva']]['votes'],'count':mapped[name][row['eva']]['count']} if row['eva'] in mapped[name] else None for name in ('shuffled','first-half','second-half')}
        candidates.append({**row,'comparisons':checks,'both_halves_unanimous_same':all(checks[name] and checks[name]['votes']==3 and checks[name]['prediction']==row['prediction'] for name in ('first-half','second-half')),
            'also_unanimous_in_shuffle':checks['shuffled']['votes']==3 and checks['shuffled']['prediction']==row['prediction']})
    # Display every occurrence of the specifically discussed word only after
    # unrestricted inference and the all-word primary ranking are complete.
    discussed={name:[{**r,'discussed_word_votes':sum(w=='vnd' for w in r['per_seed'].values())} for r in report['all_predictions'] if any(w=='vnd' for w in r['per_seed'].values())] for name,report in reports.items()}
    import gzip
    paired_initials=[]
    for seed in (3,5,7):
        with gzip.open(ROOT/'runs/actual/traces'/f'seed-{seed}.jsonl.gz','rt') as f:actual_initial=json.loads(next(f))['assignments']
        with gzip.open(ROOT/'runs/shuffled/traces'/f'seed-{seed}.jsonl.gz','rt') as f:shuffled_initial=json.loads(next(f))['assignments']
        if actual_initial!=shuffled_initial:raise ValueError('Control initial keys differ')
        paired_initials.append(seed)
    result={'paired_initial_keys_verified':paired_initials,'primary_comparison':candidates,'discussed_word_posthoc':discussed,
        'primary_sets':{name:report['primary'] for name,report in reports.items()},
        'new_chains':sum(len(r['chains']) for r in reports.values()),'proposals':sum(c['step'] for r in reports.values() for c in r['chains']),
        'search_seconds_sum':sum(c['seconds'] for r in reports.values() for c in r['chains']),
        'plaintext_accuracy':'unknown','translation_claim':False,'method':'Frozen original word-map solver, random starts only, no anchors or target-word preference'}
    write(ROOT/'summary.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['prepare','trial','inspect','summarize']);parser.add_argument('--name',choices=['actual','shuffled','first-half','second-half']);args=parser.parse_args()
    if args.stage=='prepare':prepare()
    elif args.stage=='summarize':summarize()
    else:
        if not args.name:parser.error('--name required')
        (trial if args.stage=='trial' else inspect)(args.name)
