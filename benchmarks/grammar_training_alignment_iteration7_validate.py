"""Refit source-only models and independently replay iteration-seven witnesses."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import networkx as nx

from benchmarks.grammar_training_alignment_iteration7 import (OUT, TREEBANKS, vocabulary_for, marker_groups,
    parent_groups, FixedMarkers, graph_difference, feature_audit)
from benchmarks.grammar_markers_iteration5 import marker_sentences, marker_grouped, marker_metrics, aggregate_markers
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider, score_audit
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_linker_iteration4 import detailed_metrics, summarize
from benchmarks.scalable_latin_caesar import PROIEL
from voynich_smt.training_alignment import blocked_folds, fit_graph_contrast, separability_audit
from voynich_smt.parent_ranking import ConditionalRanker, choices
from voynich_smt.marker_structure import MarkerModel, infer_attached_links, validate_markers
from voynich_smt.predicate_structure import validate_structure, morph_features
from voynich_smt.marker_structure import attachment_features
from voynich_smt.data.corpus import write_json, digest


def same_model(actual, expected):
    for k in ['weights','mean','scale']:
        assert np.allclose(getattr(actual,k),expected[k],rtol=1e-8,atol=1e-8), k


def verify_witness(saved, replay, gold):
    validate_structure(saved);validate_markers(saved,None)
    assert saved['marker_attachments']==replay['marker_attachments']
    assert saved['predicates']==gold['finite']==replay['predicates']
    if saved['status']=='optimal':
        assert replay['status']=='optimal' and saved['forest_score_integer']==replay['forest_score_integer'], (saved['forest_score_integer'],replay['status'],replay['forest_score_integer'])
        selected=0
        for c,p in saved['parents'].items():
            rows=saved['arc_candidates'][str(c)]
            selected+=round(next(r['logit'] for r in rows if r['parent']==p and r['relation']==saved['relations'][str(c)])*1e6)
        assert selected==saved['forest_score_integer']
    for c,options in saved['arc_candidates'].items():
        actual=replay['arc_candidates'][int(c)];assert len(options)==len(actual)
        for a,b in zip(options,actual):
            assert (a['parent'],a['relation'])==(b['parent'],b['relation'])
            assert math.isclose(a['logit'],b['logit'],abs_tol=1e-10)
    audit=score_audit(saved,gold)
    if audit['reference_forest_available']:
        total=0
        for c,p in gold['parents'].items():
            total+=round(next(r['logit'] for r in saved['arc_candidates'][str(c)] if r['parent']==p and r['relation']==gold['relations'][str(c)])*1e6)
        assert total==audit['reference_score_integer']
    return audit


def paired_interval(a,b,key,draws=2000):
    """Difference b minus a, resampling paired three-sentence streams."""
    assert len(a)==len(b)
    aa=np.array([[r['metrics'][key][k] for k in ['tp','predicted','gold']] for r in a])
    bb=np.array([[r['metrics'][key][k] for k in ['tp','predicted','gold']] for r in b])
    def f(x):return 2*x[...,0]/np.maximum(1,x[...,1]+x[...,2])
    rng=np.random.default_rng(1729);indices=rng.integers(0,len(a),(draws,len(a)))
    differences=f(bb[indices].sum(axis=1))-f(aa[indices].sum(axis=1))
    return {'difference':float(f(bb.sum(axis=0))-f(aa.sum(axis=0))),
        'percentile_95_interval':np.quantile(differences,[.025,.975]).tolist(),
        'draws':draws,'seed':1729,'unit':'paired three-sentence stream; descriptive within these source authors'}



def independent_replay(gold,ranker,provider,adapter):
    # Independent Edmonds optimum: super-root -> child is the ROOT option;
    # parent -> child is a non-root option. A spanning arborescence rooted
    # at the super-root is exactly an acyclic forest over all predicates.
    attached=provider.predict(gold['tokens'],gold['finite'],adapter)
    morph=[morph_features(adapter.analyze(w)) for w in gold['tokens']]
    graph=nx.DiGraph();graph.add_node(-1);options={}
    for child in gold['finite']:
        candidates=choices(gold['tokens'],child,gold['finite'],morph,typed=True,radius=None)
        features=[attachment_features(gold['tokens'],child,r['parent'],gold['finite'],morph,r['relation'],attached,False) for r in candidates]
        logits=ranker.logits(features);options[child]=[]
        for r,value in zip(candidates,logits):
            options[child].append({'parent':r['parent'],'relation':r['relation'],'logit':float(value)})
            parent=-1 if r['parent'] is None else r['parent'];weight=round(float(value)*1e6)
            # Same-endpoint relation labels cannot affect cycle feasibility.
            if not graph.has_edge(parent,child) or graph[parent][child]['weight']<weight:
                graph.add_edge(parent,child,weight=weight)
    tree=nx.maximum_spanning_arborescence(graph,preserve_attrs=True) if gold['finite'] else graph
    assert len(tree.edges)==len(gold['finite'])
    return {'status':'optimal','predicates':gold['finite'],'marker_attachments':attached,
        'arc_candidates':options,'forest_score_integer':sum(d['weight'] for _,_,d in tree.edges(data=True))}

def run():
    load=lambda n:json.loads((OUT/n).read_text())
    manifest=load('manifest.json');report=load('report.json');raw=load('models.json')
    assert digest(manifest)==report['manifest_sha256']
    for p,h in manifest['code_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['source_sha256']
    records,_=marker_sentences(path,'proiel');streams={}
    for split,lo,hi in [('train',0,400),('development',400,500),('confirmation',600,700)]:
        sentences=[]
        for author in ['Jerome','Palladius']:sentences += [s for s in records if s['author']==author][lo:hi]
        assert [s['sent_id'] for s in sentences]==manifest['source_split_ids'][split]
        streams[split]=load(split+'-truth.json')
        assert json.loads(json.dumps(marker_grouped(sentences)))==streams[split]
    train=streams['train'];adapter=FrozenAdapter(load('morphology-lattice.json'))
    authors=[PROIEL[s['sentences'][0]['work']] for s in train]
    folds=blocked_folds(authors);assert folds==manifest['fold_by_training_stream']
    for a,b in [('train','development'),('train','confirmation'),('development','confirmation')]:
        assert not set(manifest['source_split_ids'][a])&set(manifest['source_split_ids'][b])
    # Also verify confirmation excludes the previously used 500:600 cohort.
    previous=json.loads(Path('experiments/results/grammar-restoration/iteration5-v2/confirmation-truth.json').read_text())
    old_ids={x['sent_id'] for s in previous for x in s['sentences']}
    assert not old_ids&set(manifest['source_split_ids']['confirmation'])
    vocab=vocabulary_for(train);assert vocab==raw['marker_vocabulary']
    full=ConditionalRanker.fit_groups(marker_groups(train,vocab,adapter));same_model(full,raw['full_marker'])
    learned=MarkerModel(vocab,full);oof=load('oof-markers.json');fits=1
    for fold in load('crossfit-models.json'):
        held=[i for i,f in enumerate(folds) if f==fold['fold']];fitting=[i for i,f in enumerate(folds) if f!=fold['fold']]
        assert held==fold['held_streams'] and fitting==fold['fitting_streams']
        local=vocabulary_for([train[i] for i in fitting]);assert local==fold['vocabulary']
        ranker=ConditionalRanker.fit_groups(marker_groups([train[i] for i in fitting],local,adapter));same_model(ranker,fold['model'])
        model=MarkerModel(local,ranker)
        for i in held:assert model.predict(train[i]['tokens'],train[i]['finite'],adapter)==oof[i]
        fits+=1
    gold_attached=[OracleMarkerProvider(learned,s['markers'],'oracle_full').predict(s['tokens'],s['finite'],adapter) for s in train]
    models={}
    for name,attached in [('gold',gold_attached),('oof',oof)]:
        groups=parent_groups(train,attached,adapter);assert len(groups)==raw['conditional_groups'][name]
        models[name]=ConditionalRanker.fit_groups(groups);same_model(models[name],raw['parents'][name]);fits+=1
    print('Reproduced source marker/parent fits and all OOF attachments',flush=True)
    negatives=load('fitting-negatives.json');selection=[]
    for author in ['Jerome','Palladius']:selection += [i for i,a in enumerate(authors) if a==author][:40]
    assert [r['training_stream'] for r in negatives]==selection
    differences=[];replays=0;abstentions=0
    for row in negatives:
        i=row['training_stream'];gold=train[i];saved=row['prediction']
        actual=independent_replay(gold,models['gold'],FixedMarkers(gold_attached[i]),adapter)
        assert verify_witness(saved,actual,gold)==row['score_audit'];replays+=1;abstentions+=saved['status']!='optimal'
        difference=graph_difference(saved,gold,adapter,models['gold'])
        assert difference==row['difference']
        if difference is not None:
            differences.append(difference)
            # Standardization means and intercepts cancel in equal-size forests.
            expected=-row['score_audit']['optimum_minus_reference_integer']/1e6
            actual_margin=np.dot(difference,models['gold'].weights[1:])*max(1,len(gold['finite']))
            assert abs(actual_margin-expected)<len(gold['finite'])*1.1e-6
    assert len(differences)==report['optimizer_negatives_collected']
    assert separability_audit(differences)==load('fitting-separability.json')==report['separability']
    if differences:
        models['contrast']=fit_graph_contrast(models['gold'],differences);same_model(models['contrast'],raw['parents']['contrast']);fits+=1
    rows=load('predictions.json');identities=set()
    for row in rows:
        identity=(row['split'],row['stream'],row['training_markers'],row['evaluation_markers'])
        assert identity not in identities;identities.add(identity)
        gold=streams[row['split']][row['stream']];saved=row['prediction']
        provider=learned if row['evaluation_markers']=='predicted' else OracleMarkerProvider(learned,gold['markers'],'oracle_full')
        actual=independent_replay(gold,models[row['training_markers']],provider,adapter)
        try: assert verify_witness(saved,actual,gold)==row['score_audit']
        except AssertionError as exc: raise AssertionError((identity,exc.args)) from exc
        replays+=1;abstentions+=saved['status']!='optimal'
        assert detailed_metrics(saved,gold)==row['metrics']
        assert marker_metrics(saved,gold,vocab)==row['marker_metrics']
        assert feature_audit(saved,gold,adapter)==row['feature_audit']
    assert len(rows)==report['validation_predictions']==sum(len(streams[s]) for s in ['development','confirmation'])*2*len(models)
    for summary in report['summary']:
        selected=[r for r in rows if all(r[k]==summary[k] for k in ['split','training_markers','evaluation_markers'])]
        assert summarize([r['metrics'] for r in selected])==summary['metrics']
        assert aggregate_markers([r['marker_metrics'] for r in selected])==summary['markers']
        gaps=[r['score_audit']['optimum_minus_reference_integer'] for r in selected]
        assert sum(g is not None and g>0 for g in gaps)==summary['references_strictly_outscored']
        assert sum(g is not None for g in gaps)==summary['references_scored']
        assert sum(g==0 for g in gaps)==summary['references_tied']
        for outkey,inkey in [('feature_collisions','exact_feature_collisions'),('incorrect_typed_choices','wrong_typed_choices'),('incorrect_choices_feature_aliased','wrong_choices_with_identical_reference_features')]:
            assert sum(r['feature_audit'][inkey] for r in selected)==summary[outkey]
    comparisons=[]
    for evidence in ['gold','predicted']:
        for first,second in [('gold','oof'),('gold','contrast')]:
            if second not in models:continue
            select=lambda name:[r for r in rows if (r['split'],r['evaluation_markers'],r['training_markers'])==('confirmation',evidence,name)]
            a,b=select(first),select(second)
            comparisons.append({'evaluation_markers':evidence,'first':first,'second':second,
                'edges':paired_interval(a,b,'edges'),'roots':paired_interval(a,b,'roots')})
    margins={}
    for name in ['gold','contrast']:
        if name not in models:continue
        values=np.asarray(differences)@np.asarray(models[name].weights[1:])
        margins[name]={'fixed_training_negatives':len(values),'strictly_positive_margins':int(sum(values>0)),
            'minimum':float(min(values)),'mean':float(np.mean(values)),'maximum':float(max(values))}
    result={'validated':True,'source_models_refit':fits,'validation_conditions':len(rows),'forests_replayed':replays,'optimum_verifier':'independent Edmonds maximum spanning arborescence','networkx_version':nx.__version__,
        'saved_abstentions':abstentions,'paired_confirmation_intervals':comparisons,'fitting_negative_margins':margins,
        'checks':['raw source and frozen code hashes','exact disjoint source splits and unused confirmation cohort',
            'fold-local vocabulary and marker refits without held streams','two identical-budget parent refits',
            'fitting-only optimizer negatives and contrast refit','acyclic typed witnesses and optimum scores',
            'independent exact reference scores','all metrics and exact feature collisions'],
        'report_sha256':digest(report),'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'}}
    write_json(OUT/'validation.json',result)
    print('Validated',fits,'model refits;',replays,'forests;',abstentions,'saved abstentions.',flush=True)


if __name__=='__main__':run()
