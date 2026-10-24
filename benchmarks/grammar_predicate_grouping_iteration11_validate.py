"""Refit pair classifiers; exhaust partitions; independently verify forests."""
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
import z3
from benchmarks.grammar_predicate_grouping_iteration11 import (OUT,TEN,NINE,SEVEN,METHODS,GATE,pair_training,pair_metrics,summaries_for,gate_decision,selected_components)
from benchmarks.grammar_parent_interactions_iteration10 import scored_candidates
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_training_alignment_iteration7_validate import same_model,paired_interval
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider,score_audit
from benchmarks.grammar_boundary_role_iteration8 import region,masked_options,solve_options,diagnostic_counts
from benchmarks.grammar_linker_iteration4 import detailed_metrics
from voynich_smt.predicate_structure import Logistic,validate_structure
from voynich_smt.parent_ranking import ConditionalRanker
from voynich_smt.marker_structure import MarkerModel,validate_markers
from voynich_smt.predicate_grouping import predict_pairs,contiguous_groups,restrict_or_rescore,pair_probability
from voynich_smt.data.corpus import write_json,digest


def z3_optimum(pred):
    predicates=pred['predicates']
    if not predicates:return 0
    solver=z3.Optimize();solver.set(timeout=10000)
    selection={c:z3.Int('choice'+str(c)) for c in predicates};depth={c:z3.Int('depth'+str(c)) for c in predicates};terms=[]
    for c in predicates:
        rows=pred['arc_candidates'][str(c)];solver.add(selection[c]>=0,selection[c]<len(rows),depth[c]>=0,depth[c]<len(predicates))
        for i,r in enumerate(rows):
            terms.append(z3.If(selection[c]==i,round(r['logit']*1e6),0))
            if r['parent'] is not None:solver.add(z3.Implies(selection[c]==i,depth[c]>depth[r['parent']]))
    objective=solver.maximize(z3.Sum(terms));assert solver.check()==z3.sat
    assert solver.lower(objective)==solver.upper(objective)
    return solver.lower(objective).as_long()


def exhaustive_partition(predicates,probabilities):
    if not predicates:return 0.,1
    scores=[]
    for cuts in itertools.product([0,1],repeat=len(predicates)-1):
        groups=[0]
        for cut in cuts:groups.append(groups[-1]+cut)
        total=0.
        for i,a in enumerate(predicates):
            for j,b in enumerate(predicates[i+1:],i+1):
                if groups[i]==groups[j]:
                    p=min(1-1e-12,max(1e-12,pair_probability(probabilities,a,b)));total+=math.log(p/(1-p))
        scores.append(total)
    return max(scores),len(scores)


def run():
    load=lambda p:json.loads(p.read_text());manifest=load(OUT/'manifest.json');report=load(OUT/'report.json')
    assert digest(manifest)==report['manifest_sha256'] and manifest['gate']==GATE
    for p,h in {**manifest['input_sha256'],**manifest['code_sha256']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    for directory in [NINE,TEN]:
        validation=load(directory/'validation.json');assert validation['validated']
        for n,h in validation['artifact_sha256'].items():assert hashlib.sha256((directory/n).read_bytes()).hexdigest()==h
    raw=load(OUT/'models.json');adapter=FrozenAdapter(load(SEVEN/'morphology-lattice.json'))
    train=load(NINE/'train-truth.json');oof=load(NINE/'oof-markers.json');models={}
    for name in ['distance','rich']:
        x,y=pair_training(train,oof,adapter,name=='rich');model=Logistic.fit(x,y);same_model(model,raw['classifiers'][name])
        assert raw['training_counts'][name]=={'pairs':len(y),'same_sentence':sum(y),'features':len(x[0])}
        models[name]=Logistic(**raw['classifiers'][name])
    assert raw['training_counts']['rich']['pairs']==3484 and raw['training_counts']['rich']['same_sentence']==951
    rows=load(OUT/'predictions.json');pairs=load(OUT/'pairs.json');summary=summaries_for(rows)
    assert summary==report['summary'];gate=gate_decision(summary)
    assert gate==report['development_gate']==load(OUT/'development-gate.json')
    if not gate['passed']:
        assert all(r['split']=='development' for r in rows) and all(r['split']=='development' for r in pairs)
        assert not (OUT/'post-gate-inputs.json').exists()
    assert report['confirmation_evaluated']==gate['passed']
    truth={s:load(NINE/(s+'-truth.json')) for s in sorted({r['split'] for r in rows})}
    previous=load(TEN/'predictions.json');baselines={(r['stream'],r['features'],r['markers'],r['condition']):r for r in previous if r['training']=='oof'}
    parent_raw=load(TEN/'models.json')['parents'];parent_models={f:ConditionalRanker(**parent_raw['oof_'+f]) for f in ['marker_only','interactions']}
    marker_raw=load(NINE/'models.json');marker=MarkerModel(marker_raw['marker_vocabulary'],ConditionalRanker(**marker_raw['marker']))
    # Reconstruct parent logits, independently of cached candidate-score usage.
    for i,gold in enumerate(truth['development']):
        for evidence in ['gold','predicted']:
            provider=marker if evidence=='predicted' else OracleMarkerProvider(marker,gold['markers'],'oracle_full')
            for features in parent_models:
                base=baselines[i,features,evidence,'unrestricted']['prediction']
                actual=scored_candidates(base,gold,adapter,parent_models[features],provider,features=='interactions')
                assert actual['marker_attachments']==base['marker_attachments']
                for c,opts in actual['arc_candidates'].items():
                    saved=base['arc_candidates'][str(c)]
                    assert [(r['parent'],r['relation'],r['logit']) for r in opts]==[(r['parent'],r['relation'],r['logit']) for r in saved]
    probability_index={};partition_checks=0;exhaustive_cases=0
    for r in pairs:
        gold=truth[r['split']][r['stream']];base=baselines[r['stream'],'marker_only',r['markers'],'unrestricted']['prediction']
        probs=predict_pairs(gold['tokens'],gold['finite'],adapter,base['marker_attachments'],models[r['classifier']],r['classifier']=='rich')
        actual={f"{p['left']}:{p['right']}":p['probability'] for p in r['pairs']};assert probs==actual
        for p in r['pairs']:assert p['same_sentence']==int(region(p['left'],gold['boundaries'])==region(p['right'],gold['boundaries']))
        identity=(r['split'],r['stream'],r['markers'],r['classifier']);assert identity not in probability_index;probability_index[identity]=probs
        groups,score=contiguous_groups(gold['finite'],probs);best,count=exhaustive_partition(gold['finite'],probs)
        assert math.isclose(score,best,abs_tol=1e-9);partition_checks+=1;exhaustive_cases+=count
        assert [p for g in groups for p in g]==gold['finite']
    for s in report['pair_summary']:
        selected=[r for r in pairs if all(r[k]==s[k] for k in ['split','classifier','markers'])]
        assert pair_metrics(selected)=={k:v for k,v in s.items() if k not in ['split','classifier','markers']}
    index={};baseline_replays=0
    for row in rows:
        key=(row['split'],row['stream'],row['features'],row['markers'],row['method']);assert key not in index;index[key]=row
        gold=truth[row['split']][row['stream']];base=baselines[row['stream'],row['features'],row['markers'],'unrestricted']['prediction']
        method=row['method'];grouping={}
        if method=='unrestricted':expected=base
        elif method=='gold_boundaries':
            expected=dict(base);expected['arc_candidates']=masked_options(base,gold,True,False)
        else:
            name,mode=method.split('_',1);prob=probability_index[row['split'],row['stream'],row['markers'],name]
            expected,grouping=restrict_or_rescore(base,prob,mode)
        assert grouping==row['grouping']
        replay=solve_options(expected,{int(c):opts for c,opts in expected['arc_candidates'].items()});saved=row['prediction']
        validate_structure(saved);validate_markers(saved,None)
        assert saved['marker_attachments']==base['marker_attachments'] and saved['predicates']==gold['finite']
        assert saved['forest_score_integer']==replay['forest_score_integer']<=base['forest_score_integer']
        for c,options in saved['arc_candidates'].items():assert options==replay['arc_candidates'][int(c)]
        assert detailed_metrics(saved,gold)==row['metrics'] and score_audit(saved,gold)==row['audit']
        assert diagnostic_counts(saved,gold)==row['diagnostic'] and selected_components(saved)==row['selected_components']
        components=row['selected_components']
        assert abs(components['sum_float']-saved['forest_score_integer']/1e6)<=len(gold['finite'])*1e-6
        if method in ['unrestricted','gold_boundaries']:
            previous_row=baselines[row['stream'],row['features'],row['markers'],'unrestricted' if method=='unrestricted' else 'boundaries']
            assert saved['forest_score_integer']==previous_row['prediction']['forest_score_integer'] and row['metrics']==previous_row['metrics'];baseline_replays+=1
        if method.endswith('_soft') or method=='unrestricted':assert row['audit']['reference_forest_available']
    assert len(rows)==report['conditions']==2112 and len(pairs)==264
    for interval in report['paired_intervals']:
        get=lambda method:[r for r in rows if (r['split'],r['features'],r['markers'],r['method'])==(interval['split'],interval['features'],'predicted',method)]
        a,b=get(interval['first']),get(interval['second']);assert [r['stream'] for r in a]==[r['stream'] for r in b]
        assert paired_interval(a,b,'edges')==interval['edge_f1'] and paired_interval(a,b,'roots')==interval['root_f1']
    # Independent integer optimization for all modes on previously reviewed streams.
    reviewed=load(NINE/'review.json');streams=sorted({r['stream'] for r in reviewed['remaining_residuals']});z3_count=0
    for stream in streams:
        for method in METHODS:
            pred=index['development',stream,'interactions','predicted',method]['prediction']
            assert z3_optimum(pred)==pred['forest_score_integer'];z3_count+=1
    review=[];separation=[];consistency=[]
    for method in METHODS:
        counts=Counter();cases=[]
        for i,gold in enumerate(truth['development']):
            before=index['development',i,'interactions','predicted','unrestricted']['prediction']
            after=index['development',i,'interactions','predicted',method]['prediction']
            for c,reference in gold['parents'].items():
                a,b=before['parents'][c],after['parents'][c];ca,cb=a==reference,b==reference
                outcome='corrected' if cb and not ca else 'regressed' if ca and not cb else 'both_correct' if ca else 'both_wrong';counts[outcome]+=1
                if a!=b:cases.append({'stream':i,'child':int(c),'surface':gold['tokens'][int(c)],'reference_parent':reference,'before_parent':a,'after_parent':b,'outcome':outcome})
        review.append({'method':method,'counts':dict(counts),'changed_parents':cases})
    for classifier in ['distance','rich']:
        true_edges=[];selected_cross=[];violations=0;triples=0;partition_counts=Counter()
        for i,gold in enumerate(truth['development']):
            prob=probability_index['development',i,'predicted',classifier]
            for c,p in gold['parents'].items():
                if p is not None:true_edges.append(pair_probability(prob,int(c),p))
            base=index['development',i,'interactions','predicted','unrestricted']['prediction']
            for c,p in base['parents'].items():
                if p is not None and region(int(c),gold['boundaries'])!=region(p,gold['boundaries']):selected_cross.append(pair_probability(prob,int(c),p))
            for a,b,c in itertools.combinations(gold['finite'],3):
                triples+=1;violations+=sum(pair_probability(prob,x,y)>=.5 for x,y in [(a,b),(a,c),(b,c)])==2
            groups,_=contiguous_groups(gold['finite'],prob);partition_counts[len(groups)]+=1
        a,b=len(true_edges),len(selected_cross);ranks=rankdata(true_edges+selected_cross)
        separation.append({'classifier':classifier,'reference_edges':a,'baseline_selected_cross_sentence_edges':b,
            'mean_reference_probability':float(np.mean(true_edges)),'mean_selected_cross_probability':float(np.mean(selected_cross)),
            'auc_reference_vs_selected_cross':float((ranks[:a].sum()-a*(a+1)/2)/(a*b)),
            'scope':'descriptive error-conditioned sample; repeated predicates are not independent'})
        consistency.append({'classifier':classifier,'pair_filter_nontransitive_triples':int(violations),'triples':triples,
            'predicted_partition_group_counts':dict(sorted(partition_counts.items()))})
    write_json(OUT/'review.json',{'scope':'development, interaction parent model and predicted markers; mechanical comparisons',
        'parent_changes':review,'edge_conditioned_pair_separation':separation,'grouping_consistency':consistency})
    validation={'validated':True,'models_refit':2,'conditions':len(rows),'baseline_controls_reproduced':baseline_replays,
        'pair_prediction_sets':len(pairs),'partitions_exhaustively_verified':partition_checks,'partitions_enumerated':exhaustive_cases,
        'independent_Z3_conditions':z3_count,'gate_verified':gate,'report_sha256':digest(report),
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'checks':['frozen source/parent/marker/reference inputs','two source-pair logistic refits','pair labels and probabilities',
            'all contiguous partitions independently enumerated','baseline controls and frozen parent score reconstruction',
            'reference availability, exact candidate and selected/reference scores','acyclic integer optima and independent Z3',
            'all metrics, intervals and score components','failed gate leaves confirmation unevaluated']}
    write_json(OUT/'validation.json',validation)
    print('Validated',len(rows),'forests;',partition_checks,'exhaustive partition checks;',z3_count,'independent Z3 checks.',flush=True)


if __name__=='__main__':run()
