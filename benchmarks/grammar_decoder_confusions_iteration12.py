"""Nested source cross-fitting and distance-controlled hard-pair discrimination."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.stats import rankdata
from benchmarks.grammar_training_alignment_iteration7 import vocabulary_for,marker_groups
from benchmarks.grammar_parent_interactions_iteration10 import interaction_groups,scored_candidates
from benchmarks.grammar_predicate_grouping_iteration11 import TEN,NINE,SEVEN,OUT as ELEVEN
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_boundary_role_iteration8 import region,solve_options
from benchmarks.scalable_latin_caesar import PROIEL
from voynich_smt.decoder_confusions import pair_record,matched_pairs,same_child_contrasts
from voynich_smt.training_alignment import blocked_folds
from voynich_smt.predicate_grouping import pair_features
from voynich_smt.predicate_structure import Logistic,morph_features
from voynich_smt.marker_structure import MarkerModel
from voynich_smt.parent_ranking import ConditionalRanker
from voynich_smt.data.corpus import write_json,digest

OUT=Path('experiments/results/grammar-restoration/iteration12')
GATE={'minimum_matched_pairs':20,'minimum_same_child':15,'matched_auc':.60,'matched_auc_gain_over_distance':.05,
    'matched_preference':.60,'matched_preference_gain_over_distance':.10,'same_child_preference':.60,'same_child_gain_over_distance':.10}


def author(s):return PROIEL[s['sentences'][0]['work']]


def public_template(s):
    tokens=s['tokens'];predicates=s['finite'];owners=[min(predicates,key=lambda p:(abs(i-p),p)) if predicates else None for i in range(len(tokens))]
    return {'tokens':len(tokens),'predicates':predicates,'status':'unresolved','parents':{p:None for p in predicates},
        'relations':{p:None for p in predicates},'arc_candidates':{},'forest_score_integer':None,
        'token_anchors':owners,'root_groups':[None]*len(tokens),'inferred_boundaries':[],
        'known_tokens':s.get('known_tokens',0),'marker_attachments':[]}


def sample_confusions(streams,predictions):
    positive=[];negative=[]
    for i,s in enumerate(streams):
        for c,p in s['parents'].items():
            if p is not None:positive.append(pair_record(s,i,int(c),p,author(s)))
        pred=predictions[i]
        assert pred['status']=='optimal' and pred['predicates']==s['finite']
        for c,p in pred['parents'].items():
            c=int(c)
            if p is not None and region(c,s['boundaries'])!=region(p,s['boundaries']):negative.append(pair_record(s,i,c,p,author(s)))
    return {'positives':positive,'negatives':negative,'matched':matched_pairs(positive,negative),
        'same_child':same_child_contrasts(positive,negative)}


def pair_rows(records,streams,predictions,adapter,rich):
    morph={};result=[]
    for r in records:
        i=r['stream'];s=streams[i]
        if i not in morph:morph[i]=[morph_features(adapter.analyze(w)) for w in s['tokens']]
        result.append(pair_features(s['tokens'],s['finite'],morph[i],predictions[i]['marker_attachments'],r['left'],r['right'],rich))
    return result


def fit_matched_classifier(samples,streams,predictions,adapter,rich):
    matches=samples['matched']['matches'];records=[r for m in matches for r in [m['positive'],m['negative']]]
    x=pair_rows(records,streams,predictions,adapter,rich);y=[v for _ in matches for v in [1,0]]
    if not y:raise ValueError('No matched source confusions; cannot fit classifier')
    return Logistic.fit(x,y)


def score_pairs(records,streams,predictions,adapter,model,rich):
    x=pair_rows(records,streams,predictions,adapter,rich)
    return model.logits(x).tolist() if x else []


def evaluate_scores(samples,positive_logits,negative_logits):
    def auc(a,b):
        if not a or not b:return None
        n,m=len(a),len(b);r=rankdata(a+b)
        return float((sum(r[:n])-n*(n+1)/2)/(n*m))
    def preferences(contrasts):
        rows=[]
        lookup_positive={(p['stream'],p['child']):i for i,p in enumerate(samples['positives'])}
        lookup_negative={(p['stream'],p['child']):i for i,p in enumerate(samples['negatives'])}
        for c in contrasts:
            p,n=c['positive'],c['negative'];pi=lookup_positive[p['stream'],p['child']];ni=lookup_negative[n['stream'],n['child']]
            margin=positive_logits[pi]-negative_logits[ni];credit=1. if margin>1e-12 else 0. if margin< -1e-12 else .5
            rows.append({'positive_stream':p['stream'],'negative_stream':n['stream'],'positive_child':p['child'],'negative_child':n['child'],
                'margin':margin,'credit':credit})
        return {'pairs':len(rows),'accuracy':float(np.mean([r['credit'] for r in rows])) if rows else None,'rows':rows}
    matches=samples['matched']['matches'];pp=[positive_logits[m['positive_index']] for m in matches];nn=[negative_logits[m['negative_index']] for m in matches]
    margin_rows=preferences(matches);same=preferences(samples['same_child']);tight=preferences([c for c in samples['same_child'] if c['distance_matched']])
    caliper=preferences([c for c in samples['same_child'] if c['factor_two_caliper']])
    z=np.array([v for a,b in zip(pp,nn) for v in [a,b]]);y=np.tile([1.,0.],len(pp));prob=1/(1+np.exp(-np.clip(z,-40,40)))
    return {'all_selected_auc':auc(positive_logits,negative_logits),'matched_auc':auc(pp,nn),'matched_preference':margin_rows,
        'same_child_preference':same,'tight_same_child_preference':tight,'caliper_same_child_preference':caliper,
        'matched_brier':float(np.mean((prob-y)**2)),'matched_log_loss':float(np.mean(np.logaddexp(0,z)-y*z))}


def gate_decision(evaluations):
    rich=evaluations['hard_rich'];distance=evaluations['hard_distance']
    gain=lambda key:rich[key]['accuracy']-distance[key]['accuracy']
    checks={'matched_sample':rich['matched_preference']['pairs']>=GATE['minimum_matched_pairs'],
        'same_child_sample':rich['same_child_preference']['pairs']>=GATE['minimum_same_child'],
        'matched_auc':rich['matched_auc']>=GATE['matched_auc'],
        'matched_auc_gain':rich['matched_auc']-distance['matched_auc']>=GATE['matched_auc_gain_over_distance'],
        'matched_preference':rich['matched_preference']['accuracy']>=GATE['matched_preference'],
        'matched_preference_gain':gain('matched_preference')>=GATE['matched_preference_gain_over_distance'],
        'same_child_preference':rich['same_child_preference']['accuracy']>=GATE['same_child_preference'],
        'same_child_gain':gain('same_child_preference')>=GATE['same_child_gain_over_distance']}
    return {'passed':all(checks.values()),'checks':checks,'scope':'diagnostic screen on reused development; never automatic score composition'}


def run():
    if OUT.exists():raise ValueError('Preserve existing results')
    start=time.monotonic();load=lambda p:json.loads(p.read_text());train=load(NINE/'train-truth.json');dev=load(NINE/'development-truth.json')
    adapter=FrozenAdapter(load(SEVEN/'morphology-lattice.json'));folds=load(NINE/'manifest.json')['fold_by_training_stream']
    inputs=[NINE/n for n in ['manifest.json','train-truth.json','development-truth.json','validation.json']]
    inputs += [TEN/n for n in ['models.json','predictions.json','validation.json']]+[ELEVEN/'models.json',ELEVEN/'validation.json',SEVEN/'morphology-lattice.json']
    manifest={'reference_version':'predicate-complex-v1','scope':'distance-controlled discrimination only; no confirmation/target inference or score composition',
        'outer_folds':folds,'inner_folds':3,'gate':GATE,'regularization':.01,'features':{'distance':2,'rich':137},
        'matching':'same author, exact predicate gap, floor(log2 token distance), no positive reuse',
        'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/decoder_confusions.py')]}}
    write_json(OUT/'manifest.json',manifest);crossfit=[None]*len(train);fold_records=[]
    for fold in range(4):
        fit=[i for i,f in enumerate(folds) if f!=fold];held=[i for i,f in enumerate(folds) if f==fold]
        local_folds=blocked_folds([author(train[i]) for i in fit],3);inner_attached={};inner_records=[]
        for inner in range(3):
            fitting=[i for i,f in zip(fit,local_folds) if f!=inner];holding=[i for i,f in zip(fit,local_folds) if f==inner]
            vocabulary=vocabulary_for([train[i] for i in fitting]);ranker=ConditionalRanker.fit_groups(marker_groups([train[i] for i in fitting],vocabulary,adapter))
            marker=MarkerModel(vocabulary,ranker)
            for i in holding:inner_attached[i]=marker.predict(train[i]['tokens'],train[i]['finite'],adapter)
            inner_records.append({'fold':inner,'fitting_streams':fitting,'held_streams':holding,'vocabulary':vocabulary,'marker':asdict(ranker)})
        vocabulary=vocabulary_for([train[i] for i in fit]);marker_ranker=ConditionalRanker.fit_groups(marker_groups([train[i] for i in fit],vocabulary,adapter))
        marker=MarkerModel(vocabulary,marker_ranker)
        groups=interaction_groups([train[i] for i in fit],[inner_attached[i] for i in fit],adapter);parent=ConditionalRanker.fit_groups(groups)
        for i in held:
            s=train[i];observations={k:s[k] for k in ['tokens','finite']};template=public_template(observations)
            template['known_tokens']=sum(bool(adapter.analyze(w)) for w in s['tokens'])
            scored=scored_candidates(template,observations,adapter,parent,marker,True)
            crossfit[i]=solve_options(scored,scored['arc_candidates'])
        fold_records.append({'fold':fold,'fitting_streams':fit,'held_streams':held,'inner_models':inner_records,
            'vocabulary':vocabulary,'marker':asdict(marker_ranker),'parent':asdict(parent),'parent_groups':len(groups)})
        print('Outer source fold',fold,'completed',len(held),'held streams',flush=True)
    assert all(p is not None for p in crossfit)
    write_json(OUT/'crossfit-models.json',fold_records);write_json(OUT/'source-crossfit-predictions.json',crossfit)
    source_samples=sample_confusions(train,crossfit)
    previous=load(TEN/'predictions.json');devpred=[next(r['prediction'] for r in previous if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted')) for i in range(len(dev))]
    dev_samples=sample_confusions(dev,devpred);write_json(OUT/'samples.json',{'source':source_samples,'development':dev_samples})
    models={};old=load(ELEVEN/'models.json')['classifiers']
    for name,rich in [('distance',False),('rich',True)]:
        models['hard_'+name]=fit_matched_classifier(source_samples,train,crossfit,adapter,rich)
        models['all_pair_'+name]=Logistic(**old[name])
    write_json(OUT/'models.json',{k:asdict(v) for k,v in models.items()})
    predictions={};evaluations={}
    for name,model in models.items():
        rich=name.endswith('rich');p=score_pairs(dev_samples['positives'],dev,devpred,adapter,model,rich);n=score_pairs(dev_samples['negatives'],dev,devpred,adapter,model,rich)
        predictions[name]={'positive_logits':p,'negative_logits':n};evaluations[name]=evaluate_scores(dev_samples,p,n)
        print(name,'matched AUC',round(evaluations[name]['matched_auc'],3),'preference',evaluations[name]['matched_preference']['accuracy'],
            'same-child',evaluations[name]['same_child_preference']['accuracy'],flush=True)
    write_json(OUT/'predictions.json',predictions)
    decision=gate_decision(evaluations)
    sample_counts=lambda s:{'positives':len(s['positives']),'selected_cross_negatives':len(s['negatives']),'matched_pairs':len(s['matched']['matches']),
        'unmatched_negatives':len(s['matched']['unmatched_negative_indices']),'same_child':len(s['same_child']),
        'tight_same_child':sum(c['distance_matched'] for c in s['same_child'])}
    report={'manifest_sha256':digest(manifest),'source_samples':sample_counts(source_samples),'development_samples':sample_counts(dev_samples),
        'evaluations':evaluations,'development_gate':decision,'source_decoder_models_refit':20,'classifier_models_refit':2,
        'source_crossfit_forests':len(crossfit),'elapsed_seconds':time.monotonic()-start,
        'decision':'diagnostic only; no score composition, confirmation/target inference or dictionary optimization'}
    write_json(OUT/'report.json',report);print('Gate',decision,'sample counts',report['source_samples'],report['development_samples'],flush=True)


if __name__=='__main__':run()
