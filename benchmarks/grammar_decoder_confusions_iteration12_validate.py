"""Audit nested exclusion, end-to-end refits and controlled pair discrimination."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from benchmarks.grammar_decoder_confusions_iteration12 import (OUT,TEN,NINE,SEVEN,ELEVEN,GATE,author,public_template,
    sample_confusions,fit_matched_classifier,score_pairs,evaluate_scores,gate_decision)
from benchmarks.grammar_training_alignment_iteration7 import vocabulary_for,marker_groups
from benchmarks.grammar_training_alignment_iteration7_validate import same_model
from benchmarks.grammar_parent_interactions_iteration10 import interaction_groups,scored_candidates
from benchmarks.grammar_predicate_grouping_iteration11_validate import z3_optimum
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_boundary_role_iteration8 import region,solve_options
from voynich_smt.training_alignment import blocked_folds
from voynich_smt.parent_ranking import ConditionalRanker
from voynich_smt.marker_structure import MarkerModel,validate_markers
from voynich_smt.predicate_structure import Logistic,validate_structure
from voynich_smt.decoder_confusions import matched_pairs,same_child_contrasts
from voynich_smt.data.corpus import write_json,digest


def validate_sampling(sample,streams,predictions):
    for p in sample['positives']:
        s=streams[p['stream']]
        assert s['parents'].get(p['child'],s['parents'].get(str(p['child'])))==p['parent']
        assert region(p['child'],s['boundaries'])==region(p['parent'],s['boundaries'])
    for n in sample['negatives']:
        s=streams[n['stream']];prediction=predictions[n['stream']]
        assert prediction['parents'].get(n['child'],prediction['parents'].get(str(n['child'])))==n['parent']
        assert region(n['child'],s['boundaries'])!=region(n['parent'],s['boundaries'])
    assert matched_pairs(sample['positives'],sample['negatives'])==sample['matched']
    assert same_child_contrasts(sample['positives'],sample['negatives'])==sample['same_child']
    used=set();negative_used=set()
    for m in sample['matched']['matches']:
        p,n=m['positive'],m['negative'];assert (p['author'],p['predicate_gap'],p['distance_bucket'])==(n['author'],n['predicate_gap'],n['distance_bucket'])
        assert m['positive_index'] not in used and m['negative_index'] not in negative_used
        used.add(m['positive_index']);negative_used.add(m['negative_index'])
    assert negative_used|set(sample['matched']['unmatched_negative_indices'])==set(range(len(sample['negatives'])))
    return {'matched_pairs':len(used),'exact_token_distance_matches':sum(m['positive']['token_distance']==m['negative']['token_distance'] for m in sample['matched']['matches']),
        'mean_absolute_log_distance_difference':float(np.mean([m['log_distance_difference'] for m in sample['matched']['matches']])),
        'author_counts':dict(Counter(m['negative']['author'] for m in sample['matched']['matches']))}


def preference_bootstrap(evaluations,view,streams=66):
    """Paired cluster weights; matched-pool pairs may have two stream endpoints."""
    rng=np.random.default_rng(1729);weights=rng.multinomial(streams,[1/streams]*streams,size=2000)
    names=list(evaluations);reference=evaluations[names[0]][view]['rows']
    p=np.array([r['positive_stream'] for r in reference]);n=np.array([r['negative_stream'] for r in reference])
    w=weights[:,n].astype(float)
    distinct=p!=n
    w[:,distinct]*=weights[:,p[distinct]]
    denominator=w.sum(axis=1);valid=denominator>0;results={};draws={}
    for name in names:
        rows=evaluations[name][view]['rows']
        assert [(r['positive_stream'],r['negative_stream'],r['positive_child'],r['negative_child']) for r in rows]==[(r['positive_stream'],r['negative_stream'],r['positive_child'],r['negative_child']) for r in reference]
        values=np.array([r['credit'] for r in rows]);values_boot=(w[valid]@values)/denominator[valid];draws[name]=values_boot
        results[name]={'accuracy':float(np.mean(values)),'wins':sum(r['credit']==1 for r in rows),'ties':sum(r['credit']==.5 for r in rows),
            'losses':sum(r['credit']==0 for r in rows),'percentile_95_interval':np.quantile(values_boot,[.025,.975]).tolist()}
    differences={}
    for first,second in [('hard_distance','hard_rich'),('all_pair_rich','hard_rich')]:
        differences[second+'_minus_'+first]={'difference':results[second]['accuracy']-results[first]['accuracy'],
            'percentile_95_interval':np.quantile(draws[second]-draws[first],[.025,.975]).tolist()}
    return {'models':results,'paired_differences':differences,'draws':2000,'valid_draws':int(sum(valid)),'seed':1729,
        'scope':'descriptive fixed-matching stream-cluster bootstrap; product weights for distinct positive/negative stream endpoints' if view=='matched_preference' else 'descriptive paired same-child stream-cluster bootstrap'}


def run():
    load=lambda p:json.loads(p.read_text());manifest=load(OUT/'manifest.json');report=load(OUT/'report.json')
    assert digest(manifest)==report['manifest_sha256'] and manifest['gate']==GATE
    for p,h in {**manifest['input_sha256'],**manifest['code_sha256']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    for directory in [NINE,TEN,ELEVEN]:
        v=load(directory/'validation.json');assert v['validated']
        for n,h in v['artifact_sha256'].items():assert hashlib.sha256((directory/n).read_bytes()).hexdigest()==h
    train=load(NINE/'train-truth.json');dev=load(NINE/'development-truth.json');adapter=FrozenAdapter(load(SEVEN/'morphology-lattice.json'))
    folds=manifest['outer_folds'];assert folds==load(NINE/'manifest.json')['fold_by_training_stream']
    crossfit=load(OUT/'source-crossfit-predictions.json');decoder_fits=0;forests=0;z3_checks=0
    for outer in load(OUT/'crossfit-models.json'):
        fold=outer['fold'];fit=[i for i,f in enumerate(folds) if f!=fold];held=[i for i,f in enumerate(folds) if f==fold]
        assert fit==outer['fitting_streams'] and held==outer['held_streams']
        assert not set(fit)&set(held) and set(fit)|set(held)==set(range(len(train)))
        inner_folds=blocked_folds([author(train[i]) for i in fit],3);attached={}
        for inner in outer['inner_models']:
            fitting=[i for i,f in zip(fit,inner_folds) if f!=inner['fold']];holding=[i for i,f in zip(fit,inner_folds) if f==inner['fold']]
            assert fitting==inner['fitting_streams'] and holding==inner['held_streams']
            assert not (set(fitting)|set(holding))&set(held) and set(fitting)|set(holding)==set(fit)
            vocab=vocabulary_for([train[i] for i in fitting]);assert vocab==inner['vocabulary']
            ranker=ConditionalRanker.fit_groups(marker_groups([train[i] for i in fitting],vocab,adapter));same_model(ranker,inner['marker']);decoder_fits+=1
            marker=MarkerModel(vocab,ConditionalRanker(**inner['marker']))
            for i in holding:attached[i]=marker.predict(train[i]['tokens'],train[i]['finite'],adapter)
        vocab=vocabulary_for([train[i] for i in fit]);assert vocab==outer['vocabulary']
        ranker=ConditionalRanker.fit_groups(marker_groups([train[i] for i in fit],vocab,adapter));same_model(ranker,outer['marker']);decoder_fits+=1
        marker=MarkerModel(vocab,ConditionalRanker(**outer['marker']))
        groups=interaction_groups([train[i] for i in fit],[attached[i] for i in fit],adapter)
        assert len(groups)==outer['parent_groups']
        parent=ConditionalRanker.fit_groups(groups);same_model(parent,outer['parent']);decoder_fits+=1;parent=ConditionalRanker(**outer['parent'])
        selected=set()
        for a in ['Jerome','Palladius']:selected.update([i for i in held if author(train[i])==a and len(train[i]['finite'])<=8][:2])
        for i in held:
            observations={k:train[i][k] for k in ['tokens','finite']};template=public_template(observations)
            template['known_tokens']=sum(bool(adapter.analyze(w)) for w in observations['tokens'])
            scored=scored_candidates(template,observations,adapter,parent,marker,True);actual=solve_options(scored,scored['arc_candidates']);saved=crossfit[i]
            validate_structure(saved);validate_markers(saved,None)
            assert saved['predicates']==train[i]['finite'] and saved['marker_attachments']==actual['marker_attachments']
            assert saved['forest_score_integer']==actual['forest_score_integer']
            for c,opts in saved['arc_candidates'].items():assert opts==actual['arc_candidates'][int(c)]
            total=sum(round(next(r['logit'] for r in saved['arc_candidates'][c] if (r['parent'],r['relation'])==(p,saved['relations'][c]))*1e6) for c,p in saved['parents'].items())
            assert total==saved['forest_score_integer'];forests+=1
            if i in selected:assert z3_optimum(saved)==saved['forest_score_integer'];z3_checks+=1
        print('Verified nested source fold',fold,flush=True)
    assert decoder_fits==report['source_decoder_models_refit']==20 and forests==report['source_crossfit_forests']==266
    previous=load(TEN/'predictions.json');devpred=[next(r['prediction'] for r in previous if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted')) for i in range(len(dev))]
    samples=load(OUT/'samples.json')
    assert sample_confusions(train,crossfit)==samples['source'] and sample_confusions(dev,devpred)==samples['development']
    matching={'source':validate_sampling(samples['source'],train,crossfit),'development':validate_sampling(samples['development'],dev,devpred)}
    saved=load(OUT/'models.json');models={};old=load(ELEVEN/'models.json')['classifiers']
    for name,rich in [('distance',False),('rich',True)]:
        model=fit_matched_classifier(samples['source'],train,crossfit,adapter,rich);same_model(model,saved['hard_'+name])
        assert saved['all_pair_'+name]==old[name]
        models['hard_'+name]=Logistic(**saved['hard_'+name]);models['all_pair_'+name]=Logistic(**saved['all_pair_'+name])
    predictions=load(OUT/'predictions.json');evaluations={};fitting_evaluations={}
    for name,model in models.items():
        rich=name.endswith('rich');p=score_pairs(samples['development']['positives'],dev,devpred,adapter,model,rich);n=score_pairs(samples['development']['negatives'],dev,devpred,adapter,model,rich)
        assert {'positive_logits':p,'negative_logits':n}==predictions[name]
        result=evaluate_scores(samples['development'],p,n);assert result==report['evaluations'][name];evaluations[name]=result
        # Independent pairwise U-statistic for matched AUROC.
        matches=samples['development']['matched']['matches'];a=np.array([p[m['positive_index']] for m in matches]);b=np.array([n[m['negative_index']] for m in matches])
        auc=float(np.mean((a[:,None]>b[None,:])+.5*(a[:,None]==b[None,:])))
        assert abs(auc-result['matched_auc'])<1e-12
        sp=score_pairs(samples['source']['positives'],train,crossfit,adapter,model,rich);sn=score_pairs(samples['source']['negatives'],train,crossfit,adapter,model,rich)
        fit_eval=evaluate_scores(samples['source'],sp,sn)
        fitting_evaluations[name]={k:fit_eval[k] for k in ['matched_auc','matched_brier','matched_log_loss']}
        fitting_evaluations[name]['matched_preference']=fit_eval['matched_preference']['accuracy']
    assert gate_decision(evaluations)==report['development_gate']
    intervals={view:preference_bootstrap(evaluations,view,len(dev)) for view in ['matched_preference','same_child_preference']}
    write_json(OUT/'diagnostics.json',{'matching_balance':matching,'source_fitting_only':fitting_evaluations,'preference_intervals':intervals,
        'scope':'reused development diagnostic; classifier probabilities are conditional on balanced error selection, not general sentence-membership probabilities'})
    validation={'validated':True,'source_decoder_models_refit':decoder_fits,'classifier_models_refit':2,'source_crossfit_forests':forests,
        'independent_Z3_conditions':z3_checks,'sample_matching_verified':matching,'report_sha256':digest(report),
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'checks':['frozen inputs','outer/inner stream and vocabulary exclusion','twenty decoder model refits','held predictions from public observations only',
            'acyclic source witnesses, exact optima and independent Z3','reference positives and actual selected cross-sentence negatives',
            'one-to-one author/gap/distance matching and complete unmatched accounting','two matched classifier refits and frozen all-pair controls',
            'all logits/discrimination metrics and independent AUROC','screen and paired stream intervals','no decoder score composition or confirmation/target inference']}
    write_json(OUT/'validation.json',validation)
    print('Validated',decoder_fits+2,'refits;',forests,'cross-fitted source forests;',z3_checks,'Z3 checks; matched and same-child discrimination.',flush=True)


if __name__=='__main__':run()
