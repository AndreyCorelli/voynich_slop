"""Natural Latin predicate/clause recovery with target annotations held out of inference."""
from collections import Counter,defaultdict
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean
import time

from benchmarks.scalable_latin_caesar import PROIEL,PERSEUS,TREEBANKS,words
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.coherent_grammar import CoherentLatinAdapter,finite
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.predicate_structure import (StructureModel,Logistic,sentence_features,morph_features,
    parent_features,candidate_parents,validate_structure)

OUT=Path('experiments/results/grammar-restoration/iteration3-v2')
THRESHOLDS=(.2,.35,.5,.65,.8)
RATES=(0,.05,.10,.25,.50)
SEEDS=(101,202,303)
GATE={'predicate_f1':.80,'edge_f1_gain':.05}


def read_conllu(path,corpus):
    losses=Counter();result=[]
    for block in path.read_text().strip().split('\n\n'):
        meta={};raw=[];mwt=False
        for line in block.splitlines():
            if line.startswith('# ') and ' = ' in line:
                k,v=line[2:].split(' = ',1);meta[k]=v
            elif line and not line.startswith('#'):
                cols=line.split('\t')
                if '-' in cols[0]:mwt=True
                if cols[0].isdigit():raw.append(cols)
        if not raw:continue
        if mwt:losses['multiword_sentence']+=1;continue
        source=meta.get('source','').split(',')[0] if corpus=='proiel' else meta.get('sent_id','').split('.perseus-')[0]
        registry=PROIEL if corpus=='proiel' else PERSEUS|{'phi0972.phi001':'Gellius','phi0959.phi006':'Ovid'}
        author=registry.get(source)
        if author is None:raise ValueError('Unregistered source: '+source)
        kept=[c for c in raw if c[3]!='PUNCT'];forms=[words(c[1]) for c in kept]
        if any(len(f)!=1 for f in forms):losses['non_single_normalization_sentence']+=1;continue
        if not kept:continue
        index={int(c[0]):i for i,c in enumerate(kept)};raw_index={int(c[0]):c for c in raw}
        def next_kept(head):
            seen=set()
            while head and head not in index:
                if head in seen:raise ValueError('Dependency cycle')
                seen.add(head);head=int(raw_index[head][6])
            return index.get(head)
        heads=[next_kept(int(c[6])) for c in kept]
        feats=[dict(p.split('=',1) for p in c[5].split('|') if '=' in p) for c in kept]
        finite=[i for i,c in enumerate(kept) if c[3] in {'VERB','AUX'} and feats[i].get('VerbForm')=='Fin']
        def nearest(i,include):
            cursor=i if include else heads[i];seen=set()
            while cursor is not None:
                if cursor in seen:raise ValueError('Dependency cycle')
                seen.add(cursor)
                if cursor in finite:return cursor
                cursor=heads[cursor]
            return None
        result.append({'author':author,'work':source,'sent_id':meta.get('sent_id'),
            'tokens':[f[0] for f in forms],'finite':finite,'parents':{i:nearest(i,False) for i in finite},
            'anchors':[nearest(i,True) for i in range(len(kept))],
            'upos':[c[3] for c in kept],'features':feats,'heads':heads})
    return result,dict(losses)


def combine(sentences):
    tokens=[];pred=[];parents={};anchors=[];bounds=[]
    for sentence in sentences:
        off=len(tokens);tokens+=sentence['tokens'];pred += [off+i for i in sentence['finite']]
        parents.update({off+int(c):None if p is None else off+p for c,p in sentence['parents'].items()})
        anchors += [None if p is None else off+p for p in sentence['anchors']];bounds.append(len(tokens))
    return {'tokens':tokens,'finite':pred,'parents':parents,'anchors':anchors,'boundaries':bounds,
        'sentences':[{'work':s['work'],'sent_id':s['sent_id'],'tokens':len(s['tokens'])} for s in sentences]}


def prf(predicted,gold):
    predicted,gold=set(predicted),set(gold);tp=len(predicted&gold)
    precision=tp/len(predicted) if predicted else 0.;recall=tp/len(gold) if gold else 0.
    return {'tp':tp,'predicted':len(predicted),'gold':len(gold),'precision':precision,'recall':recall,
            'f1':2*tp/(len(predicted)+len(gold)) if predicted or gold else 0.}


def metrics(prediction,gold,parent_baseline=None):
    validate_structure(prediction)
    unresolved=prediction['status']!='optimal'
    effective_predicates=[] if unresolved else prediction['predicates']
    parents={} if unresolved else {int(c):p for c,p in prediction['parents'].items()}
    if parent_baseline=='root':parents={c:None for c in effective_predicates}
    if parent_baseline=='previous':
        parents={}
        for c in effective_predicates:
            allowed=[r['parent'] for r in prediction['arc_candidates'].get(c,prediction['arc_candidates'].get(str(c),[])) if r['parent'] is not None and r['parent']<c]
            parents[c]=max(allowed) if allowed else None
    truth={int(c):p for c,p in gold['parents'].items()}
    pedges={(c,p) for c,p in parents.items() if p is not None};gedges={(c,p) for c,p in truth.items() if p is not None}
    anchors=[None]*prediction['tokens'] if unresolved else prediction['token_anchors'];goldanchors=gold['anchors']
    return {'unresolved':unresolved,'predicates':prf(effective_predicates,gold['finite']),
        'edges':prf(pedges,gedges),'parent_correct':sum(c in parents and parents[c]==p for c,p in truth.items()),
        'parent_total':len(truth),'token_anchor_correct':sum(a==b and b is not None for a,b in zip(anchors,goldanchors)),
        'token_anchor_gold':sum(b is not None for b in goldanchors),'token_anchor_predicted':sum(a is not None for a in anchors),
        'tokens':len(anchors),'known_tokens':prediction['known_tokens'],
        'boundaries':prf([] if unresolved else prediction['inferred_boundaries'],gold['boundaries'][:-1])}


def aggregate(rows):
    active=rows
    if not active:return {'unresolved':0,'streams':0}
    result={'unresolved':sum(r['unresolved'] for r in rows),'streams':len(active)}
    for kind in ['predicates','edges','boundaries']:
        totals={k:sum(r[kind][k] for r in active) for k in ['tp','predicted','gold']}
        totals['precision']=totals['tp']/totals['predicted'] if totals['predicted'] else 0
        totals['recall']=totals['tp']/totals['gold'] if totals['gold'] else 0
        totals['f1']=2*totals['tp']/(totals['predicted']+totals['gold']) if totals['predicted']+totals['gold'] else 0
        result[kind]=totals
    for k in ['parent_correct','parent_total','token_anchor_correct','token_anchor_gold','token_anchor_predicted','tokens','known_tokens']:
        result[k]=sum(r[k] for r in active)
    result['parent_accuracy']=result['parent_correct']/max(1,result['parent_total'])
    result['anchor_accuracy_all_tokens']=result['token_anchor_correct']/result['tokens']
    result['anchor_accuracy_gold_covered']=result['token_anchor_correct']/max(1,result['token_anchor_gold'])
    return result


def run():
    if OUT.exists():raise ValueError('Preserve prior experiment outputs')
    start=time.monotonic()
    paths={'source':TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu',
        'development':TREEBANKS/'proiel-r2.17/la_proiel-ud-dev.conllu',
        'confirmation':TREEBANKS/'perseus-r2.17/la_perseus-ud-train.conllu'}
    datasets={};losses={}
    for k,p in paths.items():datasets[k],losses[k]=read_conllu(p,'perseus' if k=='confirmation' else 'proiel')
    sources=[]
    for author in ['Jerome','Palladius']:sources += [r for r in datasets['source'] if r['author']==author][:400]
    target_sentences={};selection=[]
    for author,key in [('Cicero','development'),('Sallust','confirmation'),('Suetonius','confirmation')]:
        selected=[];offset=0
        for s in [r for r in datasets[key] if r['author']==author]:
            begin=offset;offset+=len(s['tokens'])
            if author!='Cicero' and begin<512:continue
            if not 8<=len(s['tokens'])<=48:continue
            selected.append(s);selection.append({'author':author,'start_token_offset':begin,'sent_id':s['sent_id']})
            if len(selected)==12:break
        if len(selected)!=12:raise ValueError('Not enough declared target sentences: '+author)
        target_sentences[author]=selected
    analyzer=WhitakerAnnotator('data/vendor/whitakers-words');adapter=CoherentLatinAdapter(analyzer)
    manifest={'version':1,'gate':GATE,'finite_threshold_grid':THRESHOLDS,'source_sentences_per_author':400,
        'source_authors':['Jerome','Palladius'],'target_authors':{'development':['Cicero'],'confirmation':['Sallust','Suetonius']},
        'target_selection':selection,'losses':losses,'seeds':SEEDS,'corruption_rates':RATES,
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/predicate_structure.py')]},
        'morphology_resource':analyzer.resource,'scope':'source-supervised structure models; no target annotations in inference; short discontinuous author excerpts'}
    write_json(OUT/'manifest.json',manifest)
    # Source finite labels and dependency skeletons are the only fitting labels.
    training=[combine(sources[i:i+3]) for i in range(0,len(sources),3) if len({s['author'] for s in sources[i:i+3]})==1]
    x=[];y=[];ax=[];ay=[];source_count=Counter()
    for stream in training:
        tokens=stream['tokens'];x.extend(sentence_features(tokens,adapter));y.extend(int(i in stream['finite']) for i in range(len(tokens)))
        source_count.update(tokens);morph=[morph_features(adapter.analyze(w)) for w in tokens]
        for child in stream['finite']:
            for parent in candidate_parents(child,stream['finite']):
                ax.append(parent_features(child,parent,stream['finite'],morph));ay.append(int(parent==stream['parents'][child]))
    print('Source fitting:',len(x),'tokens,',len(ax),'candidate arcs',flush=True)
    fm=Logistic.fit(x,y);pm=Logistic.fit(ax,ay)
    targets={a:[combine(ss[i:i+3]) for i in range(0,12,3)] for a,ss in target_sentences.items()}
    # Development threshold selection uses finite labels only; source weights fixed.
    threshold_rows=[]
    for threshold in THRESHOLDS:
        predset=[];goldset=[]
        for si,s in enumerate(targets['Cicero']):
            probs=fm.probability(sentence_features(s['tokens'],adapter))
            predset.extend((si,i) for i,w in enumerate(s['tokens']) if any(finite(r) for r in adapter.analyze(w)) and probs[i]>=threshold)
            goldset.extend((si,i) for i in s['finite'])
        threshold_rows.append({'threshold':threshold,**prf(predset,goldset)})
    chosen=max(threshold_rows,key=lambda r:(r['f1'],r['threshold']))['threshold']
    model=StructureModel(adapter,fm,pm,chosen)
    write_json(OUT/'model.json',{'finite':asdict(fm),'parent':asdict(pm),'threshold':chosen,
        'training_tokens':len(x),'training_arc_candidates':len(ax),'threshold_development':threshold_rows})
    # Public streams and evaluation truth are persisted separately.
    public=[];truth=[]
    for author,streams in targets.items():
        for i,s in enumerate(streams):
            public.append({'id':f'{author}/{i}','tokens':s['tokens']})
            truth.append({'id':f'{author}/{i}','author':author,**s})
    write_json(OUT/'public.json',public);write_json(OUT/'evaluation-only-truth.json',truth)
    rows=[]
    for record,gold in zip(public,truth):
        for mode in ['latent','supplied']:
            pred=model.infer(record['tokens'],gold['boundaries'] if mode=='supplied' else None)
            baseline=model.infer(record['tokens'],gold['boundaries'] if mode=='supplied' else None,any_finite=True)
            rows.append({'id':record['id'],'author':gold['author'],'mode':mode,'prediction':pred,
                'metrics':metrics(pred,gold),'root_baseline':metrics(pred,gold,'root'),
                'previous_baseline':metrics(pred,gold,'previous'),
                'any_finite_metrics':metrics(baseline,gold)})
        print('target',record['id'],len(record['tokens']),flush=True)
    summary=[]
    for author in targets:
        for mode in ['latent','supplied']:
            rr=[r for r in rows if r['author']==author and r['mode']==mode]
            summary.append({'author':author,'mode':mode,**{k:aggregate([r[k] for r in rr]) for k in ['metrics','root_baseline','previous_baseline','any_finite_metrics']}})
    # Full-entry substitutions, preserving a global injective dictionary per stream.
    replacement_pool=[w for w,_ in source_count.most_common() if adapter.analyze(w)]
    corruption=[]
    for record,gold in zip(public,truth):
        types=sorted(set(record['tokens']))
        for seed in SEEDS:
            rng=random.Random(seed);order=types[:];rng.shuffle(order)
            available=[w for w in replacement_pool if w not in types];rng.shuffle(available)
            replacements=dict(zip(order,available));assert len(replacements)==len(types)
            for rate in RATES:
                count=round(rate*len(types));mapping={w:replacements[w] for w in order[:count]}
                altered=[mapping.get(w,w) for w in record['tokens']]
                prediction=model.infer(altered)
                corruption.append({'id':record['id'],'author':gold['author'],'seed':seed,'rate':rate,
                    'mapping':mapping,'changed_types':count,'total_types':len(types),
                    'changed_tokens':sum(w in mapping for w in record['tokens']),
                    'prediction':prediction,'metrics':metrics(prediction,gold)})
    robust=[]
    for author in targets:
        for rate in RATES:
            rr=[r for r in corruption if r['author']==author and r['rate']==rate]
            robust.append({'author':author,'rate':rate,**aggregate([r['metrics'] for r in rr])})
    held=[s for s in summary if s['author']!='Cicero' and s['mode']=='latent']
    passed=all(s['metrics'].get('predicates',{}).get('f1',0)>=GATE['predicate_f1'] and
        s['metrics'].get('edges',{}).get('f1',0)>=max(s['root_baseline'].get('edges',{}).get('f1',0),s['previous_baseline'].get('edges',{}).get('f1',0))+GATE['edge_f1_gain'] for s in held)
    write_json(OUT/'predictions.json',rows);write_json(OUT/'corruption.json',corruption)
    write_json(OUT/'source-replacement-pool.json',replacement_pool)
    used=set(source_count)|{w for r in public for w in r['tokens']}
    write_json(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in sorted(used)})
    report={'manifest_sha256':digest(manifest),'threshold':chosen,'summary':summary,'robustness':robust,
        'gate_pass':passed,'elapsed_seconds':time.monotonic()-start,'source_training_tokens':len(x),
        'streams':len(public),'target_tokens':sum(len(r['tokens']) for r in public),
        'corruption_runs':len(corruption),'decision':'partial structure measured; no dictionary search',
        'annotation_failures':analyzer.annotation_failures}
    write_json(OUT/'report.json',report)
    for s in summary:print(s['author'],s['mode'],'predicate F1',round(s['metrics']['predicates']['f1'],3),'edge F1',round(s['metrics']['edges']['f1'],3),flush=True)
    print('Gate',passed,'seconds',round(report['elapsed_seconds'],2),flush=True)


if __name__=='__main__':run()
