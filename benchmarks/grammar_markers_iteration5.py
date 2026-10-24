"""Explicit marker attachments with untouched source-confirmation evaluation."""
from collections import Counter,defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

from benchmarks.grammar_linker_iteration4 import typed_sentences,grouped,detailed_metrics,summarize,TREEBANKS,PREVIOUS,OUT as FOUR
from benchmarks.grammar_structure_iteration3 import prf
from voynich_smt.data.corpus import write_json,digest
from voynich_smt.coherent_grammar import CoherentLatinAdapter,finite
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.predicate_structure import Logistic,morph_features,sentence_features
from voynich_smt.parent_ranking import ConditionalRanker,choices,infer_links
from voynich_smt.marker_structure import MarkerModel,marker_choices,attachment_features,infer_attached_links

OUT=Path('experiments/results/grammar-restoration/iteration5-v2')
GATE={'edge_gain':.05,'root_f1_max_loss':.05,'root_recall':.80}


def marker_sentences(path,corpus):
    records,loss=typed_sentences(path,corpus);deps={}
    for block in path.read_text().strip().split('\n\n'):
        sid=None;relations=[]
        for line in block.splitlines():
            if line.startswith('# sent_id = '):sid=line[len('# sent_id = '):]
            elif line and not line.startswith('#'):
                c=line.split('\t')
                if c[0].isdigit() and c[3]!='PUNCT':relations.append(c[7].split(':')[0])
        if sid:deps[sid]=relations
    for s in records:
        markers={}
        for i,dep in enumerate(deps[s['sent_id']]):
            if dep in {'mark','cc'} and s['heads'][i] in s['finite']:
                markers[i]={'target':s['heads'][i],'kind':'coordination' if dep=='cc' else 'subordination'}
            elif s['upos'][i] in {'PRON','DET'} and s['features'][i].get('PronType')=='Rel' and s['anchors'][i] is not None:
                markers[i]={'target':s['anchors'][i],'kind':'relative'}
        s['markers']=markers
    return records,loss


def marker_grouped(sentences):
    records=grouped(sentences);parts=[sentences[i:i+3] for i in range(0,len(sentences),3)
        if len({s['author'] for s in sentences[i:i+3]})==1]
    for record,part in zip(records,parts):
        markers={};offset=0
        for s in part:
            markers.update({offset+int(i):{'target':offset+m['target'],'kind':m['kind']} for i,m in s['markers'].items()});offset+=len(s['tokens'])
        record['markers']=markers
    return records


def marker_metrics(prediction,gold,vocabulary):
    inferred={(m['position'],m['target']) for m in prediction.get('marker_attachments',[]) if m['target'] is not None}
    correct={(int(i),m['target']) for i,m in gold['markers'].items()}
    score=prf(inferred,correct)
    score['vocabulary_supported']=sum(gold['tokens'][int(i)] in vocabulary for i in gold['markers'])
    score['candidate_target_supported']=sum(gold['tokens'][int(i)] in vocabulary and m['target'] in prediction['predicates'] for i,m in gold['markers'].items())
    return score


def aggregate_markers(rows):
    sums={k:sum(r[k] for r in rows) for k in ['tp','predicted','gold','vocabulary_supported','candidate_target_supported']}
    sums.update(precision=sums['tp']/max(1,sums['predicted']),recall=sums['tp']/max(1,sums['gold']),f1=2*sums['tp']/max(1,sums['predicted']+sums['gold']))
    return sums


def run():
    if OUT.exists():raise ValueError('Preserve previous experiment')
    start=time.monotonic();path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    records,_=marker_sentences(path,'proiel');splits={}
    for split,lo,hi in [('train',0,400),('development',400,500),('confirmation',500,600)]:
        selected=[]
        for author in ['Jerome','Palladius']:selected += [s for s in records if s['author']==author][lo:hi]
        splits[split]=selected
    assert all(not ({s['sent_id'] for s in splits[a]}&{s['sent_id'] for s in splits[b]}) for a,b in [('train','development'),('train','confirmation'),('development','confirmation')])
    streams={k:marker_grouped(v) for k,v in splits.items()}
    vocabulary=defaultdict(set)
    for s in splits['train']:
        for i,m in s['markers'].items():vocabulary[s['tokens'][i]].add(m['kind'])
    vocabulary={w:sorted(k) for w,k in sorted(vocabulary.items())}
    annotator=WhitakerAnnotator('data/vendor/whitakers-words');adapter=CoherentLatinAdapter(annotator)
    old=json.loads((PREVIOUS/'model.json').read_text());four=json.loads((FOUR/'models.json').read_text())
    control=ConditionalRanker(**four['typed_conditional']);finite_model=Logistic(**old['finite'])
    manifest={'version':1,'gate':GATE,'regularization':.01,'marker_vocabulary':vocabulary,
        'split_ids':{k:[s['sent_id'] for s in v] for k,v in splits.items()},
        'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'previous_weights_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [PREVIOUS/'model.json',FOUR/'models.json']},
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/marker_structure.py')]},
        'resource':annotator.resource,'scope':'two-stage marker attachment; source-only fitting; no target tuning; source confirmation untouched until frozen'}
    write_json(OUT/'manifest.json',manifest)
    groups=[]
    for s in streams['train']:
        morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
        for i,w in enumerate(s['tokens']):
            if w not in vocabulary:continue
            options=marker_choices(s['tokens'],i,s['finite'],morph,vocabulary[w]);target=s['markers'].get(i,{}).get('target')
            index=next(j for j,r in enumerate(options) if r['target']==target)
            groups.append(([r['features'] for r in options],index))
    marker_ranker=ConditionalRanker.fit_groups(groups);marker_model=MarkerModel(vocabulary,marker_ranker)
    print('Marker fit',len(groups),'groups,',len(vocabulary),'surface forms',flush=True)
    models={};training_counts={}
    # Hard source predictions, not gold marker heads, enter the parent feature matrix.
    cache=[marker_model.predict(s['tokens'],s['finite'],adapter) for s in streams['train']]
    for name,interactions in [('marker_only',False),('marker_interactions',True)]:
        groups=[]
        for s,attachments in zip(streams['train'],cache):
            morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
            for child in s['finite']:
                options=choices(s['tokens'],child,s['finite'],morph,typed=True,radius=None)
                features=[attachment_features(s['tokens'],child,r['parent'],s['finite'],morph,r['relation'],attachments,interactions) for r in options]
                index=next(i for i,r in enumerate(options) if r['parent']==s['parents'][child] and r['relation']==s['relations'][child])
                groups.append((features,index))
        models[name]=ConditionalRanker.fit_groups(groups);training_counts[name]=len(groups)
        print('Parent fit',name,len(groups),'groups',flush=True)
    write_json(OUT/'models.json',{'marker':asdict(marker_ranker),**{n:asdict(m) for n,m in models.items()}})
    results=[]
    for split in ['development','confirmation']:
        write_json(OUT/f'{split}-truth.json',streams[split])
        for si,gold in enumerate(streams[split]):
            tokens=gold['tokens'];probs=finite_model.probability(sentence_features(tokens,adapter))
            detected=[i for i,w in enumerate(tokens) if any(finite(r) for r in adapter.analyze(w)) and probs[i]>=old['threshold']]
            for evidence,positions in [('oracle_predicates',gold['finite']),('detected',detected)]:
                for mode in ['hidden','supplied']:
                    bounds=gold['boundaries'] if mode=='supplied' else None
                    for name in ['control','marker_only','marker_interactions']:
                        if name=='control':
                            pred=infer_links(tokens,positions,adapter,control,typed=True,boundaries=bounds,radius=None)
                            # Parallel marker predictions permit a matched attachment audit;
                            # they do not affect the unchanged control forest.
                            pred['marker_attachments']=marker_model.predict(tokens,positions,adapter,bounds)
                        else:pred=infer_attached_links(tokens,positions,adapter,models[name],marker_model,
                            interactions=name=='marker_interactions',boundaries=bounds)
                        results.append({'split':split,'stream':si,'model':name,'evidence':evidence,'boundaries':mode,
                            'prediction':pred,'metrics':detailed_metrics(pred,gold),
                            'previous_baseline':detailed_metrics(pred,gold,'previous'),
                            'marker_metrics':marker_metrics(pred,gold,vocabulary)})
        print('evaluated',split,len(streams[split]),'streams',flush=True)
    summary=[]
    for split in ['development','confirmation']:
        for name in ['control','marker_only','marker_interactions']:
            for evidence in ['oracle_predicates','detected']:
                for mode in ['hidden','supplied']:
                    rr=[r for r in results if all(r[k]==v for k,v in [('split',split),('model',name),('evidence',evidence),('boundaries',mode)])]
                    summary.append({'split':split,'model':name,'evidence':evidence,'boundaries':mode,
                        'metrics':summarize([r['metrics'] for r in rr]),'previous_baseline':summarize([r['previous_baseline'] for r in rr]),
                        'markers':aggregate_markers([r['marker_metrics'] for r in rr])})
    reference=next(s for s in summary if (s['split'],s['model'],s['evidence'],s['boundaries'])==('confirmation','control','oracle_predicates','hidden'))
    gates={}
    for name in models:
        s=next(s for s in summary if (s['split'],s['model'],s['evidence'],s['boundaries'])==('confirmation',name,'oracle_predicates','hidden'))
        gates[name]=(s['metrics']['edges']['f1']>=s['previous_baseline']['edges']['f1']+GATE['edge_gain'] and
            s['metrics']['roots']['f1']>=reference['metrics']['roots']['f1']-GATE['root_f1_max_loss'] and s['metrics']['roots']['recall']>=GATE['root_recall'])
        print('fresh',name,'edge',round(s['metrics']['edges']['f1'],3),'ROOT F1',round(s['metrics']['roots']['f1'],3),'ROOT recall',round(s['metrics']['roots']['recall'],3),'gate',gates[name],flush=True)
    write_json(OUT/'source-predictions.json',results)
    # Target diagnostic is permitted only for models that pass fresh-source gate.
    target_rows=[];targets=[]
    if any(gates.values()):
        originals=json.loads((FOUR/'target-evaluation-only-truth.json').read_text());lookup={}
        for p,corpus in [(TREEBANKS/'proiel-r2.17/la_proiel-ud-dev.conllu','proiel'),(TREEBANKS/'perseus-r2.17/la_perseus-ud-train.conllu','perseus')]:
            rr,_=marker_sentences(p,corpus)
            lookup.update({(s['author'],s['sent_id']):s for s in rr})
        for original in originals:
            gold=marker_grouped([lookup[original['author'],s['sent_id']] for s in original['sentences']])[0]
            assert gold['tokens']==original['tokens'];targets.append({'id':original['id'],'author':original['author'],**gold})
        for gold in targets:
            tokens=gold['tokens'];probs=finite_model.probability(sentence_features(tokens,adapter));detected=[i for i,w in enumerate(tokens) if any(finite(r) for r in adapter.analyze(w)) and probs[i]>=old['threshold']]
            for name,passed in gates.items():
                if not passed:continue
                for evidence,positions in [('oracle_predicates',gold['finite']),('detected',detected)]:
                    for mode in ['hidden','supplied']:
                        pred=infer_attached_links(tokens,positions,adapter,models[name],marker_model,interactions=name=='marker_interactions',boundaries=gold['boundaries'] if mode=='supplied' else None)
                        target_rows.append({'id':gold['id'],'author':gold['author'],'model':name,'evidence':evidence,'boundaries':mode,'prediction':pred,'metrics':detailed_metrics(pred,gold),'marker_metrics':marker_metrics(pred,gold,vocabulary)})
        write_json(OUT/'target-evaluation-only-truth.json',targets);write_json(OUT/'target-predictions.json',target_rows)
    used={w for s in sum(streams.values(),[])+targets for w in s['tokens']}
    write_json(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in sorted(used)})
    report={'manifest_sha256':digest(manifest),'marker_training_groups':sum(w in vocabulary for s in streams['train'] for w in s['tokens']),
        'parent_training_groups':training_counts,'source_streams':{k:len(v) for k,v in streams.items()},
        'source_tokens':{k:sum(len(s['tokens']) for s in v) for k,v in streams.items()},
        'summary':summary,'fresh_gate_pass':gates,'target_models_evaluated':[n for n,p in gates.items() if p],
        'source_predictions':len(results),'target_predictions':len(target_rows),'elapsed_seconds':time.monotonic()-start,
        'decision':'keep source/target diagnostics distinct; no dictionary optimization'}
    # Record actual marker-choice group count independently of parent-group variables.
    report['marker_training_groups']=sum(w in vocabulary for s in streams['train'] for w in s['tokens'])
    write_json(OUT/'report.json',report);print('completed seconds',round(report['elapsed_seconds'],2),flush=True)


if __name__=='__main__':run()
