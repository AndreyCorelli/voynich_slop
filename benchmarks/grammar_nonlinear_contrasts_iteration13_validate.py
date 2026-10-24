"""Verify fixed nonlinear fits, construction audit and untouched holdout registry."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import numpy as np
from benchmarks.grammar_nonlinear_contrasts_iteration13 import OUT,TWELVE,NINE,SEVEN,observations,nonlinear_screen
from benchmarks.grammar_nonlinear_contrasts_iteration13_reserve import RESERVATION,strings
from benchmarks.grammar_decoder_confusions_iteration12 import pair_rows,evaluate_scores
from benchmarks.grammar_decoder_confusions_iteration12_validate import preference_bootstrap
from benchmarks.grammar_markers_iteration5 import marker_sentences,TREEBANKS
from voynich_smt.shallow_boosting import ShallowBoostedClassifier
from voynich_smt.predicate_structure import Logistic
from voynich_smt.data.corpus import write_json,digest


def audit_trees(model,x,y):
    x=np.asarray(x);y=np.asarray(y);z=np.full(len(y),model.intercept);losses=[float(np.mean(np.logaddexp(0,z)-y*z))]
    thresholds=[]
    for j in range(x.shape[1]):
        values=np.unique(x[:,j]);thresholds.append([] if len(values)<2 else ((values[1:]+values[:-1])/2).tolist() if len(values)<=5 else np.unique(np.quantile(x[:,j],[.25,.5,.75])).tolist())
    leaves=0
    for tree in model.trees:
        p=1/(1+np.exp(-np.clip(z,-40,40)));g=y-p;h=p*(1-p)
        def walk(node,indices,depth):
            nonlocal leaves
            assert depth<=2 and node['count']==len(indices)
            if 'feature' in node:
                j=node['feature'];assert 0<=j<model.feature_count and node['threshold'] in thresholds[j]
                mask=x[indices,j]<=node['threshold'];assert min(sum(mask),sum(~mask))>=20
                walk(node['left'],indices[mask],depth+1);walk(node['right'],indices[~mask],depth+1)
            else:
                leaves+=1;assert abs(node['value'])<=1
                assert np.isclose(node['gradient_sum'],g[indices].sum()) and np.isclose(node['hessian_sum'],h[indices].sum())
                assert np.isclose(node['value'],np.clip(g[indices].sum()/(h[indices].sum()+10),-1,1))
        walk(tree,np.arange(len(y)),0)
        z += .2*ShallowBoostedClassifier.tree_values(tree,x)
        loss=float(np.mean(np.logaddexp(0,z)-y*z));assert loss<=losses[-1]+1e-12;losses.append(loss)
    assert np.array_equal(z,model.logits(x))
    return {'trees':len(model.trees),'leaves':leaves,'source_logistic_loss_by_round':losses}


def run():
    load=lambda p:json.loads(p.read_text());manifest=load(OUT/'manifest.json');report=load(OUT/'report.json')
    assert digest(manifest)==report['manifest_sha256']
    for p,h in {**manifest['input_sha256'],**manifest['code_sha256']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    prior=load(TWELVE/'validation.json');assert prior['validated']
    for name,h in prior['artifact_sha256'].items():assert hashlib.sha256((TWELVE/name).read_bytes()).hexdigest()==h
    samples,train,dev,source_predictions,devpred,adapter=observations();old=load(TWELVE/'models.json')
    predictions=load(OUT/'predictions.json');models={};capacity={};evaluations={}
    config={'rounds':5,'max_depth':2,'min_leaf':20,'leaf_l2':10.,'learning_rate':.2,'max_leaf_update':1.}
    for suffix,rich in [('distance',False),('rich',True)]:
        records=[r for m in samples['source']['matched']['matches'] for r in [m['positive'],m['negative']]]
        x=pair_rows(records,train,source_predictions,adapter,rich);y=[v for _ in samples['source']['matched']['matches'] for v in [1,0]]
        assert len(x)==262 and len(x[0])==(137 if rich else 2)
        model=ShallowBoostedClassifier.fit(x,y);saved=load(OUT/('nonlinear-'+suffix+'-model.json'))
        assert asdict(model)==saved and saved['config']==config
        capacity['nonlinear_'+suffix]=audit_trees(model,x,y)
        models['nonlinear_'+suffix]=model;models['hard_'+suffix]=Logistic(**old['hard_'+suffix])
    for name,model in models.items():
        rich=name.endswith('rich');p=model.logits(pair_rows(samples['development']['positives'],dev,devpred,adapter,rich)).tolist()
        n=model.logits(pair_rows(samples['development']['negatives'],dev,devpred,adapter,rich)).tolist()
        assert {'positive_logits':p,'negative_logits':n}==predictions[name]
        evaluation=evaluate_scores(samples['development'],p,n);assert evaluation==report['evaluations'][name];evaluations[name]=evaluation
        sp=model.logits(pair_rows(samples['source']['positives'],train,source_predictions,adapter,rich)).tolist()
        sn=model.logits(pair_rows(samples['source']['negatives'],train,source_predictions,adapter,rich)).tolist()
        assert evaluate_scores(samples['source'],sp,sn)==report['source_fitting_only'][name]
        if name.startswith('hard_'):
            assert predictions[name]==load(TWELVE/'predictions.json')[name]
            assert evaluation==load(TWELVE/'report.json')['evaluations'][name]
    assert nonlinear_screen(evaluations)==report['nonlinear_screen']
    # v2 changes inclusive-threshold floating tolerance only, not fitting/predictions.
    initial=Path('experiments/results/grammar-restoration/iteration13')
    assert load(initial/'predictions.json')==predictions
    initial_manifest=load(initial/'manifest.json')
    assert hashlib.sha256((initial/'runner-original.py').read_bytes()).hexdigest()==next(h for p,h in initial_manifest['code_sha256'].items() if Path(p).name=='grammar_nonlinear_contrasts_iteration13.py')
    for suffix in ['distance','rich']:assert load(initial/('nonlinear-'+suffix+'-model.json'))==load(OUT/('nonlinear-'+suffix+'-model.json'))
    # Verify the reserved IDs are disjoint from declared research and fitting data.
    reservation=load(RESERVATION);reserved={r['sent_id'] for group in reservation['authors'].values() for r in group}
    assert len(reserved)==200
    for p,h in reservation['prior_declaration_sha256'].items():
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
        assert not reserved&set(strings(load(Path(p))))
    assert not reserved&{s['sent_id'] for stream in train+dev for s in stream['sentences']}
    path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu';assert hashlib.sha256(path.read_bytes()).hexdigest()==reservation['source_sha256']
    records,_=marker_sentences(path,'proiel');byid={s['sent_id']:s for s in records}
    for author,rows in reservation['authors'].items():
        rr=[s for s in records if s['author']==author]
        assert len(rows)==100
        for row in rows:assert rr[row['retained_position']]['sent_id']==row['sent_id'] and row['retained_position']>=700
    # Audit selection and annotated witness paths, independently of prose judgments.
    audit=load(OUT/'construction-audit.json')
    assert hashlib.sha256(Path('benchmarks/grammar_nonlinear_contrasts_iteration13_audit.py').read_bytes()).hexdigest()==audit['audit_code_sha256']
    assert audit['source_sha256']==reservation['source_sha256'] and audit['case_count']==len(audit['cases'])==20
    assert audit['families']=={'relative':10,'temporal':3,'conditional':6,'causal':1}
    for case,contrast in zip(audit['cases'],samples['development']['same_child']):
        p,n=contrast['positive'],contrast['negative'];gold=dev[p['stream']]
        assert case['stream']==p['stream'] and case['child']==p['child']==n['child']
        assert case['reference_parent']==p['parent'] and case['cross_parent']==n['parent']
        original=byid[case['sent_id']];assert case['sentence_text']==' '.join(original['tokens'])
        chain=case['ud_to_projected_parent_path'];assert chain
        for current,next_node in zip(chain,chain[1:]):assert current['head']==next_node['position']
        for node in chain:
            j=node['position'];assert node['surface']==original['tokens'][j] and node['head']==original['heads'][j] and node['upos']==original['upos'][j]
        for name,result in evaluations.items():assert case['classifier_preferences'][name]==result['same_child_preference']['rows'][case['case']-1]
        x=np.array(pair_rows([p],dev,devpred,adapter,True)[0])-np.array(pair_rows([n],dev,devpred,adapter,True)[0])
        assert case['feature_difference_counts']=={name:int(np.count_nonzero(x[lo:hi])) for name,lo,hi in [('geometry',0,2),('endpoint_windows',2,92),('between_summaries',92,122),('marker_flags',122,137)]}
    assert sum(c['family']=='relative' and bool(c['nominal_bridge_positions']) for c in audit['cases'])==audit['relative_cases_with_nominal_bridge']==7
    aliases={'hard_distance':evaluations['nonlinear_distance'],'hard_rich':evaluations['nonlinear_rich'],
        'all_pair_distance':evaluations['hard_distance'],'all_pair_rich':evaluations['hard_rich']}
    intervals={view:preference_bootstrap(aliases,view,len(dev)) for view in ['matched_preference','same_child_preference']}
    write_json(OUT/'diagnostics.json',{'capacity':capacity,'preference_intervals':intervals,
        'bootstrap_aliases':{'hard_distance':'nonlinear_distance','hard_rich':'nonlinear_rich','all_pair_distance':'linear_distance','all_pair_rich':'linear_rich'},
        'scope':'descriptive reused-development fixed-matching stream bootstrap; no held-out generalization claim'})
    validation={'validated':True,'nonlinear_models_refit':2,'linear_controls_reproduced':2,'audit_cases_verified':20,
        'reserved_sentence_ids':200,'holdout_evaluated':False,'initial_models_and_predictions_unchanged':True,
        'report_sha256':digest(report),'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'checks':['frozen samples/features/evidence','two deterministic nonlinear refits and frozen linear controls',
            'source-only thresholds, leaf sizes/depths, Newton updates and loss descent','all metrics and inclusive threshold screen',
            'unchanged predictions after numerical screen correction','twenty predetermined audit witnesses','200 reserved IDs disjoint and unscored',
            'paired stream-cluster uncertainty']}
    write_json(OUT/'validation.json',validation)
    print('Validated two nonlinear refits, two linear controls, twenty construction cases and 200 unscored reserved sentence IDs.')


if __name__=='__main__':run()
