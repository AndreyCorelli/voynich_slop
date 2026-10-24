"""Source-only pair compatibility with distance control and frozen parent scores."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.stats import rankdata
from benchmarks.grammar_parent_interactions_iteration10 import OUT as TEN,PREVIOUS as NINE,SEVEN,scored_candidates
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider,score_audit
from benchmarks.grammar_markers_iteration5 import marker_metrics
from benchmarks.grammar_linker_iteration4 import detailed_metrics,summarize
from benchmarks.grammar_boundary_role_iteration8 import region,masked_options,solve_options,diagnostic_counts
from benchmarks.grammar_training_alignment_iteration7_validate import paired_interval
from voynich_smt.parent_ranking import ConditionalRanker
from voynich_smt.marker_structure import MarkerModel
from voynich_smt.predicate_structure import Logistic,morph_features
from voynich_smt.predicate_grouping import pair_features,predict_pairs,restrict_or_rescore,pair_probability
from voynich_smt.data.corpus import write_json,digest

OUT=Path('experiments/results/grammar-restoration/iteration11')
METHODS=['unrestricted','gold_boundaries']+[f'{model}_{mode}' for model in ['distance','rich'] for mode in ['soft','pair_filter','partition']]
GATE={'primary':'rich_soft','parent_features':'interactions','markers':'predicted','gain_over_better_unrestricted_minimum':.02,
    'cross_sentence_remaining_fraction_maximum':.75,'root_recall_minimum':.8,'gain_over_distance_soft_minimum':.01}


def pair_training(streams,attached,adapter,rich):
    x=[];y=[]
    for s,markers in zip(streams,attached):
        morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
        for i,a in enumerate(s['finite']):
            for b in s['finite'][i+1:]:
                x.append(pair_features(s['tokens'],s['finite'],morph,markers,a,b,rich))
                y.append(int(region(a,s['boundaries'])==region(b,s['boundaries'])))
    return x,y


def pair_metrics(rows):
    pairs=[p for r in rows for p in r['pairs']];y=np.array([p['same_sentence'] for p in pairs]);prob=np.array([p['probability'] for p in pairs])
    predicted=prob>=.5;positive=int(sum(y));negative=len(y)-positive
    tp=int(sum(predicted&(y==1)));fp=int(sum(predicted&(y==0)));fn=positive-tp
    auc=float((rankdata(prob)[y==1].sum()-positive*(positive+1)/2)/(positive*negative)) if positive and negative else None
    return {'pairs':len(y),'positive':positive,'negative':negative,'tp':tp,'fp':fp,'fn':fn,
        'precision':tp/max(1,tp+fp),'recall':tp/max(1,positive),'f1':2*tp/max(1,2*tp+fp+fn),
        'accuracy':float(np.mean(predicted==y)),'auc':auc,'brier':float(np.mean((prob-y)**2)),
        'log_loss':float(-np.mean(y*np.log(np.clip(prob,1e-12,1))+(1-y)*np.log(np.clip(1-prob,1e-12,1))))}


def summarize_rows(rows):
    counts={k:sum(r['diagnostic'][k] for r in rows) for k in rows[0]['diagnostic']}
    for prefix in ['nonroot','ambiguous_nonroot']:counts[prefix+'_accuracy']=counts[prefix+'_correct']/max(1,counts[prefix+'_total'])
    gaps=[r['audit']['optimum_minus_reference_integer'] for r in rows]
    return {'metrics':summarize([r['metrics'] for r in rows]),'diagnostic':counts,
        'reference_available':sum(r['audit']['reference_forest_available'] for r in rows),
        'reference_scored':sum(g is not None for g in gaps),'reference_strictly_outscored':sum(g is not None and g>0 for g in gaps),
        'reference_tied':sum(g==0 for g in gaps)}


def summaries_for(rows):
    summaries=[]
    for split in sorted({r['split'] for r in rows}):
        for features in ['marker_only','interactions']:
            for markers in ['gold','predicted']:
                for method in METHODS:
                    rr=[r for r in rows if (r['split'],r['features'],r['markers'],r['method'])==(split,features,markers,method)]
                    summaries.append({'split':split,'features':features,'markers':markers,'method':method,**summarize_rows(rr)})
    return summaries


def gate_decision(summaries):
    def get(features,method):return next(s for s in summaries if (s['split'],s['features'],s['markers'],s['method'])==('development',features,'predicted',method))
    baseline=get('interactions','unrestricted');primary=get('interactions','rich_soft');distance=get('interactions','distance_soft')
    best=max(baseline['metrics']['edges']['f1'],get('marker_only','unrestricted')['metrics']['edges']['f1'])
    gain=primary['metrics']['edges']['f1']-best;distance_gain=primary['metrics']['edges']['f1']-distance['metrics']['edges']['f1']
    remaining=primary['diagnostic']['cross_sentence_choices']/max(1,baseline['diagnostic']['cross_sentence_choices'])
    recall=primary['metrics']['roots']['recall']
    checks={'gain_over_better_parent':gain>=GATE['gain_over_better_unrestricted_minimum'],
        'reduce_cross_sentence_parents':remaining<=GATE['cross_sentence_remaining_fraction_maximum'],
        'root_recall':recall>=GATE['root_recall_minimum'],'gain_over_distance':distance_gain>=GATE['gain_over_distance_soft_minimum']}
    return {'passed':all(checks.values()),'checks':checks,'gain_over_better_parent':gain,'cross_sentence_remaining_fraction':remaining,
        'root_recall':recall,'gain_over_distance':distance_gain}


def selected_components(pred):
    parent=0.;grouping=0.
    for c,p in pred['parents'].items():
        rows=pred['arc_candidates'].get(c,pred['arc_candidates'].get(str(c)))
        row=next(r for r in rows if (r['parent'],r['relation'])==(p,pred['relations'].get(c,pred['relations'].get(str(c)))))
        parent+=row.get('parent_logit',row['logit']);grouping+=row.get('grouping_log_probability',0.)
    return {'parent':parent,'grouping':grouping,'sum_float':parent+grouping,'integer_sum_of_combined_arcs':pred['forest_score_integer']}


def run():
    if OUT.exists():raise ValueError('Preserve previous results')
    start=time.monotonic();load=lambda p:json.loads(p.read_text())
    train=load(NINE/'train-truth.json');oof=load(NINE/'oof-markers.json');raw=load(NINE/'models.json')
    adapter=FrozenAdapter(load(SEVEN/'morphology-lattice.json'));marker=MarkerModel(raw['marker_vocabulary'],ConditionalRanker(**raw['marker']))
    parent_raw=load(TEN/'models.json')['parents'];parents={f:ConditionalRanker(**parent_raw['oof_'+f]) for f in ['marker_only','interactions']}
    inputs=[NINE/n for n in ['manifest.json','train-truth.json','development-truth.json','oof-markers.json','models.json','validation.json']]
    inputs += [TEN/n for n in ['models.json','predictions.json','validation.json']]+[SEVEN/'morphology-lattice.json']
    manifest={'reference_version':'predicate-complex-v1','gate':GATE,'methods':METHODS,'regularization':.01,'soft_strength':1.,'pair_threshold':.5,
        'features':'distance: 2; rich: 137; no punctuation/boundaries/roles/heads/complex membership/absolute positions/sentence count',
        'scope':'development-first source-only compatibility signal; fixed parent and marker fits; gold finite positions',
        'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/predicate_grouping.py')]}}
    write_json(OUT/'manifest.json',manifest);classifiers={};training_counts={}
    for name,rich in [('distance',False),('rich',True)]:
        x,y=pair_training(train,oof,adapter,rich);classifiers[name]=Logistic.fit(x,y)
        training_counts[name]={'pairs':len(y),'same_sentence':sum(y),'features':len(x[0])}
        print('Fit grouping',name,training_counts[name],flush=True)
    write_json(OUT/'models.json',{'classifiers':{k:asdict(m) for k,m in classifiers.items()},'training_counts':training_counts})
    previous_rows=load(TEN/'predictions.json');bases={(r['stream'],r['features'],r['markers']):r['prediction'] for r in previous_rows
        if r['split']=='development' and r['training']=='oof' and r['condition']=='unrestricted'}
    rows=[];pair_rows=[]
    def evaluate(split):
        truth=load(NINE/(split+'-truth.json'))
        for i,gold in enumerate(truth):
            for evidence in ['gold','predicted']:
                if split=='development':base_marker=bases[i,'marker_only',evidence]
                else:
                    # Template metadata depends only on tokens and oracle predicates.
                    pred=gold['finite'];owners=[min(pred,key=lambda p:(abs(p-j),p)) if pred else None for j in range(len(gold['tokens']))]
                    template={'tokens':len(gold['tokens']),'status':'unresolved','predicates':pred,'parents':{p:None for p in pred},
                        'relations':{p:None for p in pred},'token_anchors':owners,'root_groups':[None]*len(owners),'forest_score_integer':None,
                        'known_tokens':sum(bool(adapter.analyze(w)) for w in gold['tokens']),'inferred_boundaries':[],'arc_candidates':{},'marker_attachments':[]}
                    provider=marker if evidence=='predicted' else OracleMarkerProvider(marker,gold['markers'],'oracle_full')
                    base_marker=scored_candidates(template,gold,adapter,parents['marker_only'],provider,False)
                probabilities={}
                for name,model in classifiers.items():
                    probabilities[name]=predict_pairs(gold['tokens'],gold['finite'],adapter,base_marker['marker_attachments'],model,name=='rich')
                    pairs=[{'left':a,'right':b,'probability':p,'same_sentence':int(region(a,gold['boundaries'])==region(b,gold['boundaries']))}
                        for key,p in probabilities[name].items() for a,b in [map(int,key.split(':'))]]
                    pair_rows.append({'split':split,'stream':i,'markers':evidence,'classifier':name,'pairs':pairs})
                for features in ['marker_only','interactions']:
                    if split=='development':base=bases[i,features,evidence]
                    elif features=='marker_only':base=base_marker
                    else:base=scored_candidates(template,gold,adapter,parents[features],provider,True)
                    for method in METHODS:
                        grouping={}
                        if method=='unrestricted':scored=base
                        elif method=='gold_boundaries':
                            scored=deepcopy(base);scored['arc_candidates']=masked_options(base,gold,True,False)
                        else:
                            name,mode=method.split('_',1);scored,grouping=restrict_or_rescore(base,probabilities[name],mode)
                        prediction=solve_options(scored,{int(c):opts for c,opts in scored['arc_candidates'].items()})
                        rows.append({'split':split,'stream':i,'features':features,'markers':evidence,'method':method,'grouping':grouping,
                            'prediction':prediction,'metrics':detailed_metrics(prediction,gold),'audit':score_audit(prediction,gold),
                            'diagnostic':diagnostic_counts(prediction,gold),'selected_components':selected_components(prediction)})
        print('Evaluated',split,flush=True)
    evaluate('development');summaries=summaries_for(rows);decision=gate_decision(summaries)
    write_json(OUT/'development-gate.json',decision);print('Development gate',decision,flush=True)
    if decision['passed']:
        p=NINE/'confirmation-truth.json';write_json(OUT/'post-gate-inputs.json',{'confirmation_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'gate_sha256':digest(decision),'scope':'previously inspected source cohort'})
        evaluate('confirmation');summaries=summaries_for(rows)
    write_json(OUT/'pairs.json',pair_rows);write_json(OUT/'predictions.json',rows)
    pair_summary=[]
    for split in sorted({r['split'] for r in pair_rows}):
        for name in classifiers:
            for evidence in ['gold','predicted']:
                pair_summary.append({'split':split,'classifier':name,'markers':evidence,
                    **pair_metrics([r for r in pair_rows if (r['split'],r['classifier'],r['markers'])==(split,name,evidence)])})
    intervals=[]
    for split in sorted({r['split'] for r in rows}):
        for features in ['marker_only','interactions']:
            get=lambda method:[r for r in rows if (r['split'],r['features'],r['markers'],r['method'])==(split,features,'predicted',method)]
            for first,second in [('unrestricted','distance_soft'),('unrestricted','rich_soft'),('distance_soft','rich_soft')]:
                a,b=get(first),get(second);assert [r['stream'] for r in a]==[r['stream'] for r in b]
                intervals.append({'split':split,'features':features,'first':first,'second':second,
                    'edge_f1':paired_interval(a,b,'edges'),'root_f1':paired_interval(a,b,'roots')})
    report={'manifest_sha256':digest(manifest),'summary':summaries,'pair_summary':pair_summary,'paired_intervals':intervals,
        'conditions':len(rows),'models_refit':2,'development_gate':decision,'confirmation_evaluated':decision['passed'],
        'elapsed_seconds':time.monotonic()-start,'decision':'evaluate reused source confirmation' if decision['passed'] else 'stop at development; no confirmation or target evaluation'}
    write_json(OUT/'report.json',report)
    for s in summaries:
        if (s['split'],s['features'],s['markers'])==('development','interactions','predicted'):
            print(s['method'],'F1',round(s['metrics']['edges']['f1'],4),'cross-sentence',s['diagnostic']['cross_sentence_choices'],
                'gold parent reachable',s['metrics']['gold_edge_parent_reachable'],'/',s['metrics']['gold_nonroot_edges'],flush=True)


if __name__=='__main__':run()
