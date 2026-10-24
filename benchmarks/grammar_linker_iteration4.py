"""Isolate predicate linking and gate conditional ranking on source validation."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

from benchmarks.grammar_structure_iteration3 import OUT as PREVIOUS,read_conllu,combine,metrics,aggregate,prf,TREEBANKS
from voynich_smt.data.corpus import write_json,digest
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.coherent_grammar import CoherentLatinAdapter,finite
from voynich_smt.predicate_structure import Logistic,StructureModel,morph_features,sentence_features
from voynich_smt.parent_ranking import ConditionalRanker,choices,infer_links,parents_for

OUT=Path('experiments/results/grammar-restoration/iteration4')
SOURCE_GATE={'edge_gain':.05,'root_f1_max_loss':.05,'root_recall':.80}
POOLS={'three':3,'six':6,'all':None}


def typed_sentences(path,corpus):
    records,loss=read_conllu(path,corpus);relations={}
    for block in path.read_text().strip().split('\n\n'):
        sid=None;rr=[]
        for line in block.splitlines():
            if line.startswith('# sent_id = '):sid=line[len('# sent_id = '):]
            elif line and not line.startswith('#'):
                c=line.split('\t')
                if c[0].isdigit() and c[3]!='PUNCT':rr.append(c[7].split(':')[0])
        if sid:relations[sid]=rr
    for record in records:
        deps=relations[record['sent_id']];assert len(deps)==len(record['tokens'])
        kinds={}
        for child,parent in record['parents'].items():
            if parent is None:kinds[child]='root';continue
            path=[];cursor=child
            while cursor!=parent and cursor is not None:
                path.append(deps[cursor]);cursor=record['heads'][cursor]
            kinds[child]='coordination' if 'conj' in path else 'subordination'
        record['relations']=kinds
    return records,loss


def grouped(sentences):
    result=[]
    # Preserve the exact old source grouping, including exclusion of cross-author groups.
    for i in range(0,len(sentences),3):
        part=sentences[i:i+3]
        if len({s['author'] for s in part})!=1:continue
        record=combine(part);offset=0;relations={}
        for s in part:
            relations.update({offset+int(c):r for c,r in s['relations'].items()});offset+=len(s['tokens'])
        record['relations']=relations;result.append(record)
    return result


def detailed_metrics(prediction,gold,baseline=None):
    result=metrics(prediction,gold,baseline)
    parents={int(c):p for c,p in prediction['parents'].items()} if prediction['status']=='optimal' else {}
    if baseline=='root':parents={c:None for c in parents}
    if baseline=='previous':
        parents={c:max([p for p in parents_for(c,prediction['predicates'],radius=None) if p is not None and p<c],default=None) for c in parents}
        # Match the actual pool and supplied-boundary restrictions.
        for c in parents:
            options=prediction['arc_candidates'].get(c,prediction['arc_candidates'].get(str(c),[]))
            allowed=[r['parent'] for r in options if r['parent'] is not None and r['parent']<c]
            parents[c]=max(allowed,default=None)
    truth={int(c):p for c,p in gold['parents'].items()}
    result['roots']=prf([(c,None) for c,p in parents.items() if p is None],[(c,None) for c,p in truth.items() if p is None])
    relation={int(c):r for c,r in prediction.get('relations',{}).items()}
    gold_relation={int(c):r for c,r in gold['relations'].items()}
    result['typed_edges']=prf([(c,p,relation.get(c)) for c,p in parents.items() if p is not None],
        [(c,p,gold_relation[c]) for c,p in truth.items() if p is not None])
    result['gold_edge_parent_reachable']=sum(c in prediction['predicates'] and p in prediction['predicates'] and
        p in [r['parent'] for r in prediction['arc_candidates'].get(c,prediction['arc_candidates'].get(str(c),[]))]
        for c,p in truth.items() if p is not None)
    result['gold_nonroot_edges']=sum(p is not None for p in truth.values())
    return result


def summarize(rows):
    result=aggregate(rows)
    for key in ['roots','typed_edges']:
        sums={k:sum(r[key][k] for r in rows) for k in ['tp','predicted','gold']}
        sums.update(precision=sums['tp']/max(1,sums['predicted']),recall=sums['tp']/max(1,sums['gold']),
            f1=2*sums['tp']/max(1,sums['predicted']+sums['gold']))
        result[key]=sums
    result['gold_edge_parent_reachable']=sum(r['gold_edge_parent_reachable'] for r in rows)
    result['gold_nonroot_edges']=sum(r['gold_nonroot_edges'] for r in rows)
    return result


def run():
    if OUT.exists():raise ValueError('Preserve existing experiment')
    start=time.monotonic();source_path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    source,_=typed_sentences(source_path,'proiel')
    train=[];validation=[]
    for author in ['Jerome','Palladius']:
        records=[s for s in source if s['author']==author]
        train+=records[:400];validation+=records[400:500]
    assert not ({s['sent_id'] for s in train}&{s['sent_id'] for s in validation})
    training=grouped(train);valid=grouped(validation)
    annotator=WhitakerAnnotator('data/vendor/whitakers-words');adapter=CoherentLatinAdapter(annotator)
    old=json.loads((PREVIOUS/'model.json').read_text());binary=Logistic(**old['parent'])
    detector=StructureModel(adapter,Logistic(**old['finite']),binary,old['threshold'])
    manifest={'version':1,'source_gate':SOURCE_GATE,'pools':POOLS,'regularization':.01,
        'source_train_ids':[s['sent_id'] for s in train],'source_validation_ids':[s['sent_id'] for s in validation],
        'previous_model_sha256':hashlib.sha256((PREVIOUS/'model.json').read_bytes()).hexdigest(),
        'source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
        'resource':annotator.resource,'scope':'oracle diagnostic factors explicit; no target fitting or dictionary optimization',
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/parent_ranking.py')]}}
    write_json(OUT/'manifest.json',manifest)
    models={'binary':binary}
    training_counts={}
    for name,typed in [('conditional',False),('typed_conditional',True)]:
        groups=[];unreachable=0
        for s in training:
            morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
            for child in s['finite']:
                rows=choices(s['tokens'],child,s['finite'],morph,typed,radius=None)
                acceptable=[i for i,r in enumerate(rows) if r['parent']==s['parents'][child] and
                    (not typed or r['relation']==s['relations'][child])]
                if not acceptable:unreachable+=1;continue
                groups.append(([r['features'] for r in rows],acceptable[0]))
        models[name]=ConditionalRanker.fit_groups(groups)
        training_counts[name]={'groups':len(groups),'unreachable':unreachable,'candidate_rows':sum(len(f) for f,_ in groups)}
        print('fitted',name,training_counts[name],flush=True)
    write_json(OUT/'models.json',{k:asdict(m) for k,m in models.items()})
    write_json(OUT/'source-validation-truth.json',valid)
    source_rows=[]
    for si,gold in enumerate(valid):
        tokens=gold['tokens']
        probs=detector.finite_model.probability(sentence_features(tokens,adapter))
        detected=[i for i,w in enumerate(tokens) if any(finite(r) for r in adapter.analyze(w)) and probs[i]>=detector.threshold]
        for evidence,predicates in [('oracle_predicates',gold['finite']),('detected',detected)]:
            for mode in ['hidden','supplied']:
                bounds=gold['boundaries'] if mode=='supplied' else None
                for name,ranker in models.items():
                    pred=infer_links(tokens,predicates,adapter,ranker,typed=name=='typed_conditional',boundaries=bounds,radius=None)
                    source_rows.append({'stream':si,'model':name,'evidence':evidence,'boundaries':mode,
                        'prediction':pred,'metrics':detailed_metrics(pred,gold),
                        'previous_baseline':detailed_metrics(pred,gold,'previous'),'root_baseline':detailed_metrics(pred,gold,'root')})
    source_summary=[]
    for name in models:
        for evidence in ['oracle_predicates','detected']:
            for mode in ['hidden','supplied']:
                chosen=[r for r in source_rows if r['model']==name and r['evidence']==evidence and r['boundaries']==mode]
                source_summary.append({'model':name,'evidence':evidence,'boundaries':mode,
                    **{key:summarize([r[key] for r in chosen]) for key in ['metrics','previous_baseline','root_baseline']}})
    reference=next(s for s in source_summary if s['model']=='binary' and s['evidence']=='oracle_predicates' and s['boundaries']=='hidden')
    gates={}
    for name in ['conditional','typed_conditional']:
        s=next(s for s in source_summary if s['model']==name and s['evidence']=='oracle_predicates' and s['boundaries']=='hidden')
        gates[name]=(s['metrics']['edges']['f1']>=s['previous_baseline']['edges']['f1']+SOURCE_GATE['edge_gain'] and
            s['metrics']['roots']['f1']>=reference['metrics']['roots']['f1']-SOURCE_GATE['root_f1_max_loss'] and
            s['metrics']['roots']['recall']>=SOURCE_GATE['root_recall'])
        print('source validation',name,'edge F1',round(s['metrics']['edges']['f1'],3),'ROOT F1',round(s['metrics']['roots']['f1'],3),
            'ROOT recall',round(s['metrics']['roots']['recall'],3),'gate',gates[name],flush=True)
    write_json(OUT/'source-validation-predictions.json',source_rows)
    # Target sentence IDs/tokens remain exactly those of iteration 3.
    target_original=json.loads((PREVIOUS/'evaluation-only-truth.json').read_text())
    lookup={}
    target_paths=[(TREEBANKS/'proiel-r2.17/la_proiel-ud-dev.conllu','proiel'),
                  (TREEBANKS/'perseus-r2.17/la_perseus-ud-train.conllu','perseus')]
    for path,corpus in target_paths:
        records,_=typed_sentences(path,corpus)
        for s in records:lookup[s['author'],s['sent_id']]=s
    targets=[]
    for record in target_original:
        sentences=[lookup[record['author'],s['sent_id']] for s in record['sentences']]
        gold=grouped(sentences)[0];assert gold['tokens']==record['tokens']
        assert gold['finite']==record['finite'] and {str(k):v for k,v in gold['parents'].items()}==record['parents']
        targets.append({'id':record['id'],'author':record['author'],**gold})
    write_json(OUT/'target-evaluation-only-truth.json',targets)
    allowed_models={'binary':binary}|{n:models[n] for n,p in gates.items() if p}
    target_rows=[]
    for gold in targets:
        tokens=gold['tokens'];probs=detector.finite_model.probability(sentence_features(tokens,adapter))
        detected=[i for i,w in enumerate(tokens) if any(finite(r) for r in adapter.analyze(w)) and probs[i]>=detector.threshold]
        for evidence,predicates in [('oracle_predicates',gold['finite']),('detected',detected)]:
            for mode in ['hidden','supplied']:
                for pool,radius in POOLS.items():
                    for name,ranker in allowed_models.items():
                        pred=infer_links(tokens,predicates,adapter,ranker,typed=name=='typed_conditional',
                            boundaries=gold['boundaries'] if mode=='supplied' else None,radius=radius)
                        target_rows.append({'id':gold['id'],'author':gold['author'],'model':name,'evidence':evidence,'boundaries':mode,'pool':pool,
                            'prediction':pred,'metrics':detailed_metrics(pred,gold),
                            'previous_baseline':detailed_metrics(pred,gold,'previous'),'root_baseline':detailed_metrics(pred,gold,'root')})
    summary=[]
    for author in ['Cicero','Sallust','Suetonius']:
        for name in allowed_models:
            for evidence in ['oracle_predicates','detected']:
                for mode in ['hidden','supplied']:
                    for pool in POOLS:
                        rr=[r for r in target_rows if r['author']==author and r['model']==name and r['evidence']==evidence and r['boundaries']==mode and r['pool']==pool]
                        summary.append({'author':author,'model':name,'evidence':evidence,'boundaries':mode,'pool':pool,
                            **{k:summarize([r[k] for r in rr]) for k in ['metrics','previous_baseline','root_baseline']}})
    write_json(OUT/'target-predictions.json',target_rows)
    used={w for s in training+valid+targets for w in s['tokens']}
    write_json(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in sorted(used)})
    report={'manifest_sha256':digest(manifest),'training_counts':training_counts,'source_gate_pass':gates,
        'source_validation_streams':len(valid),'source_validation_tokens':sum(len(s['tokens']) for s in valid),
        'source_summary':source_summary,'target_summary':summary,'target_models_evaluated':list(allowed_models),
        'source_predictions':len(source_rows),'target_predictions':len(target_rows),
        'elapsed_seconds':time.monotonic()-start,'decision':'no dictionary search; source gate enforced before target model evaluation'}
    write_json(OUT/'report.json',report)
    print('completed',len(source_rows),'source and',len(target_rows),'target predictions; seconds',round(report['elapsed_seconds'],2),flush=True)


if __name__=='__main__':run()
