"""Versioned source-only reference repair and matched-reference parent refits."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from benchmarks.grammar_training_alignment_iteration7 import (OUT as PREVIOUS, vocabulary_for,marker_groups,parent_groups)
from benchmarks.grammar_markers_iteration5 import marker_sentences,marker_grouped,marker_metrics,aggregate_markers,TREEBANKS
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider,score_audit
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_linker_iteration4 import detailed_metrics,summarize
from benchmarks.grammar_boundary_role_iteration8 import CONDITIONS,masked_options,solve_options,diagnostic_counts,summarize_rows
from voynich_smt.predicate_projection import VERSION,project_sentence,projection_changes
from voynich_smt.parent_ranking import ConditionalRanker,choices
from voynich_smt.marker_structure import MarkerModel,attachment_features
from voynich_smt.predicate_structure import morph_features
from voynich_smt.data.corpus import write_json,digest

OUT=Path('experiments/results/grammar-restoration/iteration9')


def source_references():
    path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    records,_=marker_sentences(path,'proiel');deps={}
    for block in path.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid:
            deps[sid]=[l.split('\t')[7] for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
    ids=json.loads((PREVIOUS/'manifest.json').read_text())['source_split_ids'];byid={r['sent_id']:r for r in records}
    sentences={};streams={};audits={}
    for split,sids in ids.items():
        original=[byid[sid] for sid in sids]
        revised=[project_sentence(s,deps[s['sent_id']]) for s in original]
        sentences[split]=revised;streams[split]=marker_grouped(revised)
        assert json.loads(json.dumps(marker_grouped(original)))==json.loads((PREVIOUS/(split+'-truth.json')).read_text())
        audits[split]=[projection_changes(a,b) for a,b in zip(original,revised)]
        for a,b in zip(marker_grouped(original),streams[split]):
            assert a['tokens']==b['tokens'] and a['finite']==b['finite'] and a['boundaries']==b['boundaries'] and a['sentences']==b['sentences']
    return sentences,streams,audits


def audit_summary(audits):
    summaries={}
    for split,changes in audits.items():
        counts=Counter()
        for c in changes:
            counts['sentences']+=1
            for key in ['parents','relations','markers','anchors','complexes']:
                counts[key]+=len(c[key]);counts['sentences_with_'+key]+=bool(c[key])
            counts['marker_added']+=sum(m['old'] is None for m in c['markers'])
            counts['marker_removed']+=sum(m['new'] is None for m in c['markers'])
            counts['marker_retargeted_or_retyped']+=sum(m['old'] is not None and m['new'] is not None for m in c['markers'])
            counts['sentences_with_issues']+=bool(c['issues'])
        summaries[split]={'counts':dict(counts),'issues':dict(Counter(i['kind'] for c in changes for i in c['issues']))}
    return summaries


def scored_candidates(template,gold,adapter,ranker,provider):
    """Gold is used only for tokens/explicit oracle predicate positions here."""
    pred=deepcopy(template);tokens=gold['tokens'];predicates=gold['finite']
    attached=provider.predict(tokens,predicates,adapter);morph=[morph_features(adapter.analyze(w)) for w in tokens];options={}
    for child in predicates:
        rows=choices(tokens,child,predicates,morph,typed=True,radius=None)
        x=[attachment_features(tokens,child,r['parent'],predicates,morph,r['relation'],attached,False) for r in rows]
        logits=ranker.logits(x);normalizer=float(np.logaddexp.reduce(logits))
        options[child]=[{'parent':r['parent'],'relation':r['relation'],'logit':float(value),
            'conditional_probability':float(np.exp(value-normalizer))} for r,value in zip(rows,logits)]
    pred.update(arc_candidates=options,marker_attachments=attached)
    return pred


def run():
    if OUT.exists():raise ValueError('Preserve previous output')
    start=time.monotonic();load=lambda n:json.loads((PREVIOUS/n).read_text())
    sentences,streams,audits=source_references();adapter=FrozenAdapter(load('morphology-lattice.json'))
    inputs=['manifest.json','models.json','morphology-lattice.json','train-truth.json','development-truth.json','confirmation-truth.json','predictions.json','validation.json']
    manifest={'reference_version':VERSION,'scope':'same source-only cohorts; confirmation already inspected; no target evaluation or dictionary search',
        'regularization':.01,'features':'unchanged 249 marker-only; gold predicates; full parent pool',
        'source_split_ids':load('manifest.json')['source_split_ids'],'fold_by_training_stream':load('manifest.json')['fold_by_training_stream'],
        'input_sha256':{str(PREVIOUS/n):hashlib.sha256((PREVIOUS/n).read_bytes()).hexdigest() for n in inputs},
        'source_sha256':hashlib.sha256((TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu').read_bytes()).hexdigest(),
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/predicate_projection.py')]},
        'evaluation_marker_provider':'same revised-reference full-source marker model for every compared parent model'}
    write_json(OUT/'manifest.json',manifest)
    for split,gold in streams.items():write_json(OUT/(split+'-truth.json'),gold)
    write_json(OUT/'projection-audit.json',audits)
    # Retain sentence-level component membership and ambiguity, which grouping strips.
    write_json(OUT/'sentence-complexes.json',{k:[{x:s[x] for x in ['sent_id','predicate_complexes','projection_issues']} for s in ss] for k,ss in sentences.items()})
    vocab=vocabulary_for(streams['train']);marker_ranker=ConditionalRanker.fit_groups(marker_groups(streams['train'],vocab,adapter))
    marker=MarkerModel(vocab,marker_ranker);folds=manifest['fold_by_training_stream'];oof=[None]*len(folds);fold_records=[]
    for fold in range(4):
        fit=[i for i,f in enumerate(folds) if f!=fold];held=[i for i,f in enumerate(folds) if f==fold]
        local=vocabulary_for([streams['train'][i] for i in fit]);ranker=ConditionalRanker.fit_groups(marker_groups([streams['train'][i] for i in fit],local,adapter))
        provider=MarkerModel(local,ranker)
        for i in held:oof[i]=provider.predict(streams['train'][i]['tokens'],streams['train'][i]['finite'],adapter)
        fold_records.append({'fold':fold,'fitting_streams':fit,'held_streams':held,'vocabulary':local,'model':asdict(ranker)})
        print('Revised marker fold',fold,flush=True)
    attached_gold=[OracleMarkerProvider(marker,s['markers'],'oracle_full').predict(s['tokens'],s['finite'],adapter) for s in streams['train']]
    legacy=load('models.json');models={};group_counts={}
    for name,attached in [('gold',attached_gold),('oof',oof)]:
        groups=parent_groups(streams['train'],attached,adapter);group_counts[name]=len(groups)
        models['revised_'+name]=ConditionalRanker.fit_groups(groups)
        models['legacy_'+name]=ConditionalRanker(**legacy['parents'][name])
        print('Revised parent',name,len(groups),'groups',flush=True)
    write_json(OUT/'models.json',{'marker_vocabulary':vocab,'marker':asdict(marker_ranker),'parents':{k:asdict(v) for k,v in models.items()},'group_counts':group_counts})
    write_json(OUT/'crossfit-models.json',fold_records);write_json(OUT/'oof-markers.json',oof)
    oldrows=load('predictions.json');templates={(r['split'],r['stream']):r['prediction'] for r in oldrows if r['training_markers']=='gold' and r['evaluation_markers']=='gold'}
    rows=[]
    for split in ['development','confirmation']:
        for i,gold in enumerate(streams[split]):
            for evidence,provider in [('gold',OracleMarkerProvider(marker,gold['markers'],'oracle_full')),('predicted',marker)]:
                for name,ranker in models.items():
                    scored=scored_candidates(templates[split,i],gold,adapter,ranker,provider)
                    for condition,(bounds,roles) in CONDITIONS.items():
                        pred=solve_options(scored,masked_options(scored,gold,bounds,roles))
                        rows.append({'split':split,'stream':i,'model':name,'markers':evidence,'condition':condition,
                            'prediction':pred,'metrics':detailed_metrics(pred,gold),'audit':score_audit(pred,gold),
                            'diagnostic':diagnostic_counts(pred,gold),'marker_metrics':marker_metrics(pred,gold,vocab)})
        print('Evaluated',split,flush=True)
    write_json(OUT/'predictions.json',rows)
    summaries=[]
    for split in ['development','confirmation']:
        for name in models:
            for evidence in ['gold','predicted']:
                for condition in CONDITIONS:
                    rr=[r for r in rows if (r['split'],r['model'],r['markers'],r['condition'])==(split,name,evidence,condition)]
                    summaries.append({'split':split,'model':name,'markers':evidence,'condition':condition,
                        **summarize_rows(rr),'marker_metrics':aggregate_markers([r['marker_metrics'] for r in rr])})
    # Label-only audit: same completed legacy predictions under both references.
    rescored=[]
    for split in ['development','confirmation']:
        oldtruth=load(split+'-truth.json')
        for name in ['gold','oof']:
            base=[r for r in oldrows if (r['split'],r['training_markers'],r['evaluation_markers'])==(split,name,'gold')]
            for version,truth in [('legacy',oldtruth),(VERSION,streams[split])]:
                rescored.append({'split':split,'model':'legacy_'+name,'evaluation_reference':version,
                    'unchanged_predictions':True,'original_abstentions_retained':True,
                    'metrics':summarize([detailed_metrics(r['prediction'],truth[r['stream']]) for r in base])})
    report={'manifest_sha256':digest(manifest),'reference_version':VERSION,'audit':audit_summary(audits),'summary':summaries,
        'unchanged_prediction_rescoring':rescored,'conditions':len(rows),'models_refit':7,
        'elapsed_seconds':time.monotonic()-start,'decision':'reference repair/source-only diagnosis; no target or lexical restoration claim'}
    write_json(OUT/'report.json',report)
    for s in summaries:
        if (s['split'],s['markers'])==('confirmation','gold') and s['condition'] in ['unrestricted','both']:
            print(s['model'],s['condition'],'F1',round(s['metrics']['edges']['f1'],4),'ambiguous',round(s['diagnostic']['ambiguous_nonroot_accuracy'],4),flush=True)
    print('Audit',report['audit'],'seconds',round(report['elapsed_seconds'],2),flush=True)


if __name__=='__main__':run()
