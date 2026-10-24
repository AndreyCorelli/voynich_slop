"""Development-gated ablation of existing candidate-parent marker features."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from benchmarks.grammar_predicate_complex_iteration9 import OUT as PREVIOUS
from benchmarks.grammar_training_alignment_iteration7 import OUT as SEVEN
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider,score_audit
from benchmarks.grammar_markers_iteration5 import marker_metrics,aggregate_markers
from benchmarks.grammar_linker_iteration4 import detailed_metrics
from benchmarks.grammar_boundary_role_iteration8 import CONDITIONS,masked_options,solve_options,diagnostic_counts,summarize_rows
from benchmarks.grammar_training_alignment_iteration7_validate import paired_interval
from voynich_smt.parent_ranking import ConditionalRanker,choices
from voynich_smt.marker_structure import MarkerModel,attachment_features
from voynich_smt.predicate_structure import morph_features
from voynich_smt.data.corpus import write_json,digest

OUT=Path('experiments/results/grammar-restoration/iteration10')
GATE={'ambiguous_gold_both_gain':.05,'ambiguous_predicted_both_gain_strictly_positive':True,
    'predicted_unrestricted_f1_gain_minimum':0.,'predicted_unrestricted_root_recall_minimum':.8,
    'primary_training':'oof'}


def interaction_groups(streams,attachments,adapter):
    result=[]
    for s,attached in zip(streams,attachments):
        morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
        for child in s['finite']:
            options=choices(s['tokens'],child,s['finite'],morph,typed=True,radius=None)
            rows=[attachment_features(s['tokens'],child,r['parent'],s['finite'],morph,r['relation'],attached,True) for r in options]
            parent=s['parents'].get(child,s['parents'].get(str(child)));kind=s['relations'].get(child,s['relations'].get(str(child)))
            answer=next(i for i,r in enumerate(options) if (r['parent'],r['relation'])==(parent,kind))
            result.append((rows,answer))
    return result


def scored_candidates(template,gold,adapter,ranker,provider,interactions):
    result=deepcopy(template);attached=provider.predict(gold['tokens'],gold['finite'],adapter)
    morph=[morph_features(adapter.analyze(w)) for w in gold['tokens']];options={}
    for child in gold['finite']:
        rows=choices(gold['tokens'],child,gold['finite'],morph,typed=True,radius=None)
        x=[attachment_features(gold['tokens'],child,r['parent'],gold['finite'],morph,r['relation'],attached,interactions) for r in rows]
        logits=ranker.logits(x);normalizer=float(np.logaddexp.reduce(logits))
        options[child]=[{'parent':r['parent'],'relation':r['relation'],'logit':float(v),
            'conditional_probability':float(np.exp(v-normalizer))} for r,v in zip(rows,logits)]
    result.update(arc_candidates=options,marker_attachments=attached)
    return result


def summaries_for(rows):
    result=[]
    for split in sorted({r['split'] for r in rows}):
        for training in ['gold','oof']:
            for features in ['marker_only','interactions']:
                for markers in ['gold','predicted']:
                    for condition in CONDITIONS:
                        rr=[r for r in rows if (r['split'],r['training'],r['features'],r['markers'],r['condition'])==(split,training,features,markers,condition)]
                        result.append({'split':split,'training':training,'features':features,'markers':markers,'condition':condition,
                            **summarize_rows(rr),'marker_metrics':aggregate_markers([r['marker_metrics'] for r in rr])})
    return result


def gate_decision(summaries):
    def get(features,markers,condition):
        return next(s for s in summaries if (s['split'],s['training'],s['features'],s['markers'],s['condition'])==('development','oof',features,markers,condition))
    a,b=get('marker_only','gold','both'),get('interactions','gold','both')
    gold_gain=b['diagnostic']['ambiguous_nonroot_accuracy']-a['diagnostic']['ambiguous_nonroot_accuracy']
    a,b=get('marker_only','predicted','both'),get('interactions','predicted','both')
    predicted_gain=b['diagnostic']['ambiguous_nonroot_accuracy']-a['diagnostic']['ambiguous_nonroot_accuracy']
    a,b=get('marker_only','predicted','unrestricted'),get('interactions','predicted','unrestricted')
    f1_gain=b['metrics']['edges']['f1']-a['metrics']['edges']['f1'];root_recall=b['metrics']['roots']['recall']
    checks={'gold_both_parent_gain':gold_gain>=GATE['ambiguous_gold_both_gain'],
        'predicted_both_parent_gain':predicted_gain>0,'predicted_unrestricted_non_degradation':f1_gain>=0,
        'predicted_unrestricted_root_recall':root_recall>=GATE['predicted_unrestricted_root_recall_minimum']}
    return {'passed':all(checks.values()),'checks':checks,'gold_both_ambiguous_parent_gain':gold_gain,
        'predicted_both_ambiguous_parent_gain':predicted_gain,'predicted_unrestricted_f1_gain':f1_gain,
        'predicted_unrestricted_root_recall':root_recall}


def paired_comparisons(rows):
    results=[]
    for split in sorted({r['split'] for r in rows}):
        for training in ['gold','oof']:
            for evidence in ['gold','predicted']:
                for mode in ['unrestricted','both']:
                    get=lambda features:[r for r in rows if (r['split'],r['training'],r['features'],r['markers'],r['condition'])==(split,training,features,evidence,mode)]
                    a,b=get('marker_only'),get('interactions')
                    assert [r['stream'] for r in a]==[r['stream'] for r in b]
                    results.append({'split':split,'training':training,'markers':evidence,'condition':mode,
                        'edge_f1':paired_interval(a,b,'edges'),'root_f1':paired_interval(a,b,'roots')})
    return results


def run():
    if OUT.exists():raise ValueError('Preserve previous results')
    started=time.monotonic();load=lambda n:json.loads((PREVIOUS/n).read_text());raw=load('models.json')
    adapter=FrozenAdapter(json.loads((SEVEN/'morphology-lattice.json').read_text()));train=load('train-truth.json')
    marker=MarkerModel(raw['marker_vocabulary'],ConditionalRanker(**raw['marker']))
    inputs=[PREVIOUS/n for n in ['manifest.json','models.json','train-truth.json','development-truth.json','oof-markers.json','review.json','validation.json']]
    inputs += [SEVEN/'morphology-lattice.json']
    manifest={'reference_version':load('manifest.json')['reference_version'],'gate':GATE,'scope':'development-first source-only fixed-feature ablation',
        'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/marker_structure.py')]},
        'features':{'marker_only':249,'interactions':282},'regularization':.01,'marker_models':'frozen iteration9; OOF fitting unchanged',
        'no_target_evaluation':True,'no_dictionary_optimization':True}
    write_json(OUT/'manifest.json',manifest)
    gold_attached=[OracleMarkerProvider(marker,s['markers'],'oracle_full').predict(s['tokens'],s['finite'],adapter) for s in train]
    oof=load('oof-markers.json');models={};counts={}
    for training,attached in [('gold',gold_attached),('oof',oof)]:
        groups=interaction_groups(train,attached,adapter);counts[training]=len(groups)
        models[training,'interactions']=ConditionalRanker.fit_groups(groups)
        models[training,'marker_only']=ConditionalRanker(**raw['parents']['revised_'+training])
        print('Fit',training,len(groups),'groups',flush=True)
    write_json(OUT/'models.json',{'parents':{t+'_'+f:asdict(m) for (t,f),m in models.items()},'group_counts':counts})
    previous_rows=load('predictions.json');rows=[]
    def evaluate(split):
        truth=load(split+'-truth.json')
        for i,gold in enumerate(truth):
            template=next(r['prediction'] for r in previous_rows if (r['split'],r['stream'],r['model'],r['markers'],r['condition'])==(split,i,'revised_gold','gold','unrestricted'))
            for training in ['gold','oof']:
                for evidence,provider in [('gold',OracleMarkerProvider(marker,gold['markers'],'oracle_full')),('predicted',marker)]:
                    for features in ['marker_only','interactions']:
                        scored=scored_candidates(template,gold,adapter,models[training,features],provider,features=='interactions')
                        for condition,(bounds,roles) in CONDITIONS.items():
                            prediction=solve_options(scored,masked_options(scored,gold,bounds,roles))
                            rows.append({'split':split,'stream':i,'training':training,'features':features,'markers':evidence,'condition':condition,
                                'prediction':prediction,'metrics':detailed_metrics(prediction,gold),'audit':score_audit(prediction,gold),
                                'diagnostic':diagnostic_counts(prediction,gold),'marker_metrics':marker_metrics(prediction,gold,marker.vocabulary)})
        print('Evaluated',split,flush=True)
    evaluate('development');summaries=summaries_for(rows);decision=gate_decision(summaries)
    write_json(OUT/'development-gate.json',decision);print('Development gate',decision,flush=True)
    if decision['passed']:
        # Record the input checksum only after the development decision.
        path=PREVIOUS/'confirmation-truth.json'
        write_json(OUT/'post-gate-inputs.json',{'confirmation_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'gate_sha256':digest(decision),'scope':'previously inspected cohort; no fresh-confirmation claim'})
        evaluate('confirmation');summaries=summaries_for(rows)
    write_json(OUT/'predictions.json',rows)
    report={'manifest_sha256':digest(manifest),'summary':summaries,'development_gate':decision,'conditions':len(rows),
        'models_refit':2,'paired_comparisons':paired_comparisons(rows),'confirmation_evaluated':decision['passed'],
        'elapsed_seconds':time.monotonic()-started,'decision':'evaluate reused source confirmation' if decision['passed'] else 'stop at development; do not evaluate interaction model on confirmation'}
    write_json(OUT/'report.json',report)
    for s in summaries:
        if s['training']=='oof' and s['condition'] in ['unrestricted','both']:
            print(s['split'],s['features'],s['markers'],s['condition'],'edge',round(s['metrics']['edges']['f1'],4),
                'ambiguous',s['diagnostic']['ambiguous_nonroot_correct'],'/',s['diagnostic']['ambiguous_nonroot_total'],flush=True)


if __name__=='__main__':run()
