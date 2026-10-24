"""Source-only gold/OOF parent-training matrix with optimized-forest contrasts."""
from collections import Counter,defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import time
import numpy as np

from benchmarks.grammar_markers_iteration5 import marker_sentences,marker_grouped,marker_metrics,aggregate_markers,TREEBANKS
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider,score_audit
from benchmarks.grammar_linker_iteration4 import detailed_metrics,summarize
from benchmarks.scalable_latin_caesar import PROIEL
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.coherent_grammar import CoherentLatinAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.predicate_structure import morph_features
from voynich_smt.parent_ranking import ConditionalRanker,choices
from voynich_smt.marker_structure import MarkerModel,marker_choices,attachment_features,infer_attached_links
from voynich_smt.training_alignment import blocked_folds,fit_graph_contrast,separability_audit

OUT=Path('experiments/results/grammar-restoration/iteration7')


def vocabulary_for(streams):
    vocabulary=defaultdict(set)
    for s in streams:
        for i,m in s['markers'].items():vocabulary[s['tokens'][int(i)]].add(m['kind'])
    return {w:sorted(k) for w,k in sorted(vocabulary.items())}


def marker_groups(streams,vocabulary,adapter):
    result=[]
    for s in streams:
        morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
        for i,w in enumerate(s['tokens']):
            if w not in vocabulary:continue
            options=marker_choices(s['tokens'],i,s['finite'],morph,vocabulary[w]);target=s['markers'].get(i,s['markers'].get(str(i),{})).get('target')
            index=next(j for j,r in enumerate(options) if r['target']==target)
            result.append(([r['features'] for r in options],index))
    return result


class FixedMarkers:
    def __init__(self,attachments):self.attachments=attachments
    def predict(self,tokens,predicates,adapter,boundaries=None):
        if boundaries is not None:raise ValueError('This fitting/diagnostic provider has no oracle boundaries')
        return self.attachments


def parent_groups(streams,attached,adapter):
    groups=[]
    for s,markers in zip(streams,attached):
        morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
        for child in s['finite']:
            options=choices(s['tokens'],child,s['finite'],morph,typed=True,radius=None)
            features=[attachment_features(s['tokens'],child,r['parent'],s['finite'],morph,r['relation'],markers,False) for r in options]
            parent=s['parents'].get(child,s['parents'].get(str(child)));relation=s['relations'].get(child,s['relations'].get(str(child)))
            index=next(i for i,r in enumerate(options) if r['parent']==parent and r['relation']==relation)
            groups.append((features,index))
    return groups


def feature_audit(prediction,gold,adapter):
    morph=[morph_features(adapter.analyze(w)) for w in gold['tokens']];attached=prediction['marker_attachments']
    exact=0;choices_total=0;wrong_parents=0;errors_aliased=0
    for child in gold['finite']:
        parent=gold['parents'].get(child,gold['parents'].get(str(child)));kind=gold['relations'].get(child,gold['relations'].get(str(child)))
        reference=np.asarray(attachment_features(gold['tokens'],child,parent,gold['finite'],morph,kind,attached,False))
        options=choices(gold['tokens'],child,gold['finite'],morph,typed=True,radius=None)
        aliases=[]
        for r in options:
            if r['parent']==parent and r['relation']==kind:continue
            other=np.asarray(attachment_features(gold['tokens'],child,r['parent'],gold['finite'],morph,r['relation'],attached,False))
            same=np.array_equal(reference,other);exact+=same;choices_total+=1
            if same:aliases.append((r['parent'],r['relation']))
        if prediction['status']=='optimal':
            guessed=prediction['parents'].get(child,prediction['parents'].get(str(child)))
            guessed_kind=prediction['relations'].get(child,prediction['relations'].get(str(child)))
            if (guessed,guessed_kind)!=(parent,kind):
                wrong_parents+=1;errors_aliased+=(guessed,guessed_kind) in aliases
    return {'alternative_choices':choices_total,'exact_feature_collisions':int(exact),'wrong_typed_choices':wrong_parents,
        'wrong_choices_with_identical_reference_features':int(errors_aliased),
        'scope':'exact feature equality only; unique position/distance values do not prove linguistic sufficiency'}


def graph_difference(prediction,gold,adapter,scaler):
    if prediction['status']!='optimal':return None
    morph=[morph_features(adapter.analyze(w)) for w in gold['tokens']];attached=prediction['marker_attachments']
    difference=np.zeros(len(scaler.scale));wrong=False
    for child in gold['finite']:
        parent=gold['parents'].get(child,gold['parents'].get(str(child)));relation=gold['relations'].get(child,gold['relations'].get(str(child)))
        guessed=prediction['parents'].get(child,prediction['parents'].get(str(child)));kind=prediction['relations'].get(child,prediction['relations'].get(str(child)))
        wrong|=(parent,relation)!=(guessed,kind)
        correct=np.array(attachment_features(gold['tokens'],child,parent,gold['finite'],morph,relation,attached,False))
        other=np.array(attachment_features(gold['tokens'],child,guessed,gold['finite'],morph,kind,attached,False))
        difference+=(correct-other)/np.asarray(scaler.scale)
    return (difference/max(1,len(gold['finite']))).tolist() if wrong else None


def run():
    if OUT.exists():raise ValueError('Preserve previous experiment')
    started=time.monotonic();path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    records,_=marker_sentences(path,'proiel');split_sentences={}
    for name,lo,hi in [('train',0,400),('development',400,500),('confirmation',600,700)]:
        selected=[]
        for author in ['Jerome','Palladius']:
            ss=[s for s in records if s['author']==author][lo:hi]
            if len(ss)!=hi-lo:raise ValueError('Insufficient declared source sentences')
            selected+=ss
        split_sentences[name]=selected
    assert all(not ({s['sent_id'] for s in split_sentences[a]}&{s['sent_id'] for s in split_sentences[b]}) for a,b in [('train','development'),('train','confirmation'),('development','confirmation')])
    streams={k:marker_grouped(ss) for k,ss in split_sentences.items()}
    authors=[PROIEL[s['sentences'][0]['work']] for s in streams['train']];folds=blocked_folds(authors)
    annotator=WhitakerAnnotator('data/vendor/whitakers-words');adapter=CoherentLatinAdapter(annotator)
    vocabulary=vocabulary_for(streams['train'])
    manifest={'version':1,'regularization':.01,'parent_features':'iteration5 marker-only; same full parent pool; gold finite positions; hidden boundaries',
        'source_split_ids':{k:[s['sent_id'] for s in ss] for k,ss in split_sentences.items()},
        'fold_by_training_stream':folds,'folds':4,'negative_budget_per_author':40,
        'scope':'source-only diagnostic matrix; no target-author reads, no selection on confirmation',
        'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'resource':annotator.resource,
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/training_alignment.py')]}}
    write_json(OUT/'manifest.json',manifest)
    for split,gold in streams.items():write_json(OUT/f'{split}-truth.json',gold)
    full_marker_ranker=ConditionalRanker.fit_groups(marker_groups(streams['train'],vocabulary,adapter))
    full_marker=MarkerModel(vocabulary,full_marker_ranker)
    oof=[None]*len(streams['train']);fold_records=[]
    for fold in range(4):
        fitting=[i for i,f in enumerate(folds) if f!=fold];held=[i for i,f in enumerate(folds) if f==fold]
        fold_vocabulary=vocabulary_for([streams['train'][i] for i in fitting])
        ranker=ConditionalRanker.fit_groups(marker_groups([streams['train'][i] for i in fitting],fold_vocabulary,adapter))
        marker=MarkerModel(fold_vocabulary,ranker)
        for i in held:oof[i]=marker.predict(streams['train'][i]['tokens'],streams['train'][i]['finite'],adapter)
        fold_records.append({'fold':fold,'fitting_streams':fitting,'held_streams':held,'vocabulary':fold_vocabulary,'model':asdict(ranker)})
        print('OOF',fold,len(fitting),'fit,',len(held),'held',flush=True)
    assert all(m is not None for m in oof)
    gold_attached=[OracleMarkerProvider(full_marker,s['markers'],'oracle_full').predict(s['tokens'],s['finite'],adapter) for s in streams['train']]
    marker_training={'gold':gold_attached,'oof':oof};models={};groups_count={}
    for name,attachments in marker_training.items():
        groups=parent_groups(streams['train'],attachments,adapter)
        models[name]=ConditionalRanker.fit_groups(groups);groups_count[name]=len(groups)
        print('parent',name,len(groups),'groups',flush=True)
    write_json(OUT/'crossfit-models.json',fold_records);write_json(OUT/'oof-markers.json',oof)
    # Collect fitting-only actual optimizer negatives before evaluating validation.
    selection=[]
    for author in ['Jerome','Palladius']:selection += [i for i,a in enumerate(authors) if a==author][:40]
    negative_rows=[];differences=[]
    for i in selection:
        gold=streams['train'][i];prediction=infer_attached_links(gold['tokens'],gold['finite'],adapter,models['gold'],FixedMarkers(gold_attached[i]),interactions=False)
        difference=graph_difference(prediction,gold,adapter,models['gold'])
        if difference is not None:differences.append(difference)
        negative_rows.append({'training_stream':i,'prediction':prediction,'difference':difference,'score_audit':score_audit(prediction,gold)})
    if differences:models['contrast']=fit_graph_contrast(models['gold'],differences)
    separability=separability_audit(differences)
    write_json(OUT/'fitting-negatives.json',negative_rows);write_json(OUT/'fitting-separability.json',separability)
    print('negatives',len(differences),'/',len(selection),'linear feasibility',separability['status'],flush=True)
    write_json(OUT/'models.json',{'full_marker':asdict(full_marker_ranker),'marker_vocabulary':vocabulary,
        'parents':{k:asdict(m) for k,m in models.items()},'conditional_groups':groups_count})
    rows=[]
    for split in ['development','confirmation']:
        for i,gold in enumerate(streams[split]):
            for evidence,provider in [('gold',OracleMarkerProvider(full_marker,gold['markers'],'oracle_full')),('predicted',full_marker)]:
                for name,ranker in models.items():
                    prediction=infer_attached_links(gold['tokens'],gold['finite'],adapter,ranker,provider,interactions=False)
                    rows.append({'split':split,'stream':i,'training_markers':name,'evaluation_markers':evidence,
                        'prediction':prediction,'metrics':detailed_metrics(prediction,gold),
                        'marker_metrics':marker_metrics(prediction,gold,vocabulary),'score_audit':score_audit(prediction,gold),
                        'feature_audit':feature_audit(prediction,gold,adapter)})
        print('evaluated',split,flush=True)
    write_json(OUT/'predictions.json',rows)
    summary=[]
    for split in ['development','confirmation']:
        for training in models:
            for evidence in ['gold','predicted']:
                rr=[r for r in rows if (r['split'],r['training_markers'],r['evaluation_markers'])==(split,training,evidence)]
                audits=[r['score_audit'] for r in rr]
                summary.append({'split':split,'training_markers':training,'evaluation_markers':evidence,
                    'metrics':summarize([r['metrics'] for r in rr]),'markers':aggregate_markers([r['marker_metrics'] for r in rr]),
                    'references_scored':sum(a['optimum_minus_reference_integer'] is not None for a in audits),
                    'references_strictly_outscored':sum(a['optimum_minus_reference_integer'] is not None and a['optimum_minus_reference_integer']>0 for a in audits),
                    'references_tied':sum(a['optimum_minus_reference_integer']==0 for a in audits),
                    'feature_collisions':sum(r['feature_audit']['exact_feature_collisions'] for r in rr),
                    'incorrect_typed_choices':sum(r['feature_audit']['wrong_typed_choices'] for r in rr),
                    'incorrect_choices_feature_aliased':sum(r['feature_audit']['wrong_choices_with_identical_reference_features'] for r in rr)})
    used={w for ss in streams.values() for s in ss for w in s['tokens']}
    write_json(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in sorted(used)})
    report={'manifest_sha256':digest(manifest),'summary':summary,'source_streams':{k:len(v) for k,v in streams.items()},
        'source_tokens':{k:sum(len(s['tokens']) for s in v) for k,v in streams.items()},'validation_predictions':len(rows),
        'optimizer_negative_budget':len(selection),'optimizer_negatives_collected':len(differences),'separability':separability,
        'contrast_budget_note':'one fitting-only collection round and anchored pairwise refit; extra budget, not matched to main arms',
        'elapsed_seconds':time.monotonic()-started,'decision':'source-only diagnosis; no target evaluation or dictionary optimization'}
    write_json(OUT/'report.json',report)
    for s in summary:
        if s['split']=='confirmation':print(s['training_markers'],s['evaluation_markers'],'edge F1',round(s['metrics']['edges']['f1'],3),
            'ROOT F1',round(s['metrics']['roots']['f1'],3),'wrong references',s['references_strictly_outscored'],'/',s['references_scored'],flush=True)
    print('completed seconds',round(report['elapsed_seconds'],2),flush=True)


if __name__=='__main__':run()
