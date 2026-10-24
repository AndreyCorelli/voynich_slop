"""Independent source refits, explicit-marker witnesses and forest replay."""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import math
import random
import numpy as np

from benchmarks.grammar_markers_iteration5 import (OUT,GATE,marker_sentences,marker_grouped,marker_metrics,aggregate_markers,TREEBANKS,FOUR,PREVIOUS)
from benchmarks.grammar_linker_iteration4 import detailed_metrics,summarize
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.predicate_structure import Logistic,morph_features,sentence_features,validate_structure
from voynich_smt.coherent_grammar import finite
from voynich_smt.parent_ranking import ConditionalRanker,choices,infer_links
from voynich_smt.marker_structure import (MarkerModel,marker_choices,attachment_features,infer_attached_links,validate_markers)


def run():
    load=lambda n:json.loads((OUT/n).read_text())
    manifest=load('manifest.json');report=load('report.json');raw=load('models.json')
    assert digest(manifest)==report['manifest_sha256'] and manifest['gate']==GATE
    for p,h in {**manifest['code_sha256'],**manifest['previous_weights_sha256']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['source_sha256']
    source,_=marker_sentences(path,'proiel');lookup={s['sent_id']:s for s in source}
    ids=manifest['split_ids']
    assert all(not (set(ids[a])&set(ids[b])) for a,b in [('train','development'),('train','confirmation'),('development','confirmation')])
    splits={k:[lookup[sid] for sid in ss] for k,ss in ids.items()}
    assert all({s['author'] for s in ss}=={'Jerome','Palladius'} for ss in splits.values())
    for author in ['Jerome','Palladius']:
        author_source=[s for s in source if s['author']==author]
        for name,lo,hi in [('train',0,400),('development',400,500),('confirmation',500,600)]:
            assert [s['sent_id'] for s in splits[name] if s['author']==author]==[s['sent_id'] for s in author_source[lo:hi]]
    grouped={k:marker_grouped(ss) for k,ss in splits.items()}
    for name in ['development','confirmation']:assert json.loads(json.dumps(grouped[name]))==load(f'{name}-truth.json')
    vocabulary={}
    for s in splits['train']:
        for i,m in s['markers'].items():vocabulary.setdefault(s['tokens'][i],set()).add(m['kind'])
    vocabulary={w:sorted(k) for w,k in vocabulary.items()};assert vocabulary==manifest['marker_vocabulary']
    adapter=FrozenAdapter(load('morphology-lattice.json'));groups=[]
    for s in grouped['train']:
        morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
        for i,w in enumerate(s['tokens']):
            if w not in vocabulary:continue
            rows=marker_choices(s['tokens'],i,s['finite'],morph,vocabulary[w]);target=s['markers'].get(i,{}).get('target')
            index=next(j for j,r in enumerate(rows) if r['target']==target)
            groups.append(([r['features'] for r in rows],index))
    marker_ranker=ConditionalRanker.fit_groups(groups)
    def compare(fit,saved):
        for key in ['weights','mean','scale']:assert np.allclose(getattr(fit,key),saved[key],rtol=1e-8,atol=1e-8)
    compare(marker_ranker,raw['marker']);assert len(groups)==report['marker_training_groups']
    marker_model=MarkerModel(vocabulary,ConditionalRanker(**raw['marker']))
    cache=[marker_model.predict(s['tokens'],s['finite'],adapter) for s in grouped['train']]
    models={}
    for name,interactions in [('marker_only',False),('marker_interactions',True)]:
        groups=[]
        for s,attached in zip(grouped['train'],cache):
            morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
            for child in s['finite']:
                rows=choices(s['tokens'],child,s['finite'],morph,typed=True,radius=None)
                features=[attachment_features(s['tokens'],child,r['parent'],s['finite'],morph,r['relation'],attached,interactions) for r in rows]
                index=next(i for i,r in enumerate(rows) if r['parent']==s['parents'][child] and r['relation']==s['relations'][child])
                groups.append((features,index))
        fit=ConditionalRanker.fit_groups(groups);compare(fit,raw[name]);models[name]=ConditionalRanker(**raw[name])
        assert len(groups)==report['parent_training_groups'][name]
    control=ConditionalRanker(**json.loads((FOUR/'models.json').read_text())['typed_conditional'])
    old=json.loads((PREVIOUS/'model.json').read_text());detector=Logistic(**old['finite']);checked=0
    def verify(row,gold):
        nonlocal checked
        saved=row['prediction'];validate_structure(saved)
        boundaries=gold['boundaries'] if row['boundaries']=='supplied' else None
        validate_markers(saved,boundaries)
        probs=detector.probability(sentence_features(gold['tokens'],adapter))
        detected=[i for i,w in enumerate(gold['tokens']) if any(finite(r) for r in adapter.analyze(w)) and probs[i]>=old['threshold']]
        positions=gold['finite'] if row['evidence']=='oracle_predicates' else detected
        assert positions==saved['predicates']
        attached=marker_model.predict(gold['tokens'],positions,adapter,boundaries)
        assert attached==saved['marker_attachments']
        if row['model']=='control':replay=infer_links(gold['tokens'],positions,adapter,control,typed=True,boundaries=boundaries,radius=None)
        else:replay=infer_attached_links(gold['tokens'],positions,adapter,models[row['model']],marker_model,interactions=row['model']=='marker_interactions',boundaries=boundaries)
        assert replay['status']==saved['status'] and replay['forest_score_integer']==saved['forest_score_integer']
        for child,parent in saved['parents'].items():
            options=saved['arc_candidates'][child];actual=replay['arc_candidates'][int(child)]
            assert len(options)==len(actual)
            for a,b in zip(options,actual):
                assert a['parent']==b['parent'] and a['relation']==b['relation'] and math.isclose(a['logit'],b['logit'],abs_tol=1e-10)
            if saved['status']=='optimal':assert any(r['parent']==parent and r['relation']==saved['relations'][child] for r in options)
            if boundaries and parent is not None:
                region=lambda p:next(i for i,b in enumerate(boundaries) if p<b)
                assert region(int(child))==region(parent)
        if saved['status']=='optimal':
            score=sum(round(next(r['logit'] for r in saved['arc_candidates'][c] if r['parent']==p and r['relation']==saved['relations'][c])*1000000) for c,p in saved['parents'].items())
            assert score==saved['forest_score_integer']
        assert detailed_metrics(saved,gold)==row['metrics']
        if 'previous_baseline' in row:assert detailed_metrics(saved,gold,'previous')==row['previous_baseline']
        assert marker_metrics(saved,gold,vocabulary)==row['marker_metrics']
        checked+=1
    rows=load('source-predictions.json')
    for row in rows:verify(row,grouped[row['split']][row['stream']])
    for summary in report['summary']:
        selected=[r for r in rows if all(r[k]==summary[k] for k in ['split','model','evidence','boundaries'])]
        assert summarize([r['metrics'] for r in selected])==summary['metrics']
        assert summarize([r['previous_baseline'] for r in selected])==summary['previous_baseline']
        assert aggregate_markers([r['marker_metrics'] for r in selected])==summary['markers']
    reference=next(s for s in report['summary'] if (s['split'],s['model'],s['evidence'],s['boundaries'])==('confirmation','control','oracle_predicates','hidden'))
    gates={}
    for name in models:
        s=next(s for s in report['summary'] if (s['split'],s['model'],s['evidence'],s['boundaries'])==('confirmation',name,'oracle_predicates','hidden'))
        gates[name]=(s['metrics']['edges']['f1']>=s['previous_baseline']['edges']['f1']+GATE['edge_gain'] and
            s['metrics']['roots']['f1']>=reference['metrics']['roots']['f1']-GATE['root_f1_max_loss'] and s['metrics']['roots']['recall']>=GATE['root_recall'])
    assert gates==report['fresh_gate_pass']
    allowed={n for n,p in gates.items() if p};assert set(report['target_models_evaluated'])==allowed
    target_rows=[]
    if allowed:
        truth={r['id']:r for r in load('target-evaluation-only-truth.json')};target_rows=load('target-predictions.json')
        originals={r['id']:r for r in json.loads((FOUR/'target-evaluation-only-truth.json').read_text())}
        for k,gold in truth.items():
            for field in ['tokens','finite','parents','boundaries']:assert gold[field]==originals[k][field]
        assert {r['model'] for r in target_rows}==allowed
        for row in target_rows:verify(row,truth[row['id']])
    assert len(rows)==report['source_predictions'] and len(target_rows)==report['target_predictions']
    # Paired cluster intervals on fresh confirmation only, without model selection.
    intervals=[]
    for name in models:
        selected=[r for r in rows if (r['split'],r['model'],r['evidence'],r['boundaries'])==('confirmation',name,'oracle_predicates','hidden')]
        rng=random.Random(20261021);draws=[]
        for _ in range(1000):
            sample=rng.choices(selected,k=len(selected))
            def f1(key):
                tp=sum(r[key]['edges']['tp'] for r in sample);den=sum(r[key]['edges']['predicted']+r[key]['edges']['gold'] for r in sample)
                return 2*tp/den if den else 0
            draws.append(f1('metrics')-f1('previous_baseline'))
        draws.sort();intervals.append({'model':name,'interval':[draws[24],draws[974]],'seed':20261021,'resamples':1000})
    write_json(OUT/'paired-confirmation-intervals.json',intervals)
    write_json(OUT/'validation.json',{'validated':True,'forest_replays':checked,'source_models_refitted':3,
        'fresh_source_gates':gates,'target_models':sorted(allowed),'report_sha256':digest(report),
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'checks':['source-only marker vocabulary and exact model refits','three-way disjoint source IDs','single marker target and predicate/marker exclusion',
                  'acyclic forest optimum and typed witness','fresh-source gate precedes target models','all scores, ROOT/nonroot/marker metrics and baselines']})
    print('Validated',checked,'forests and marker attachments; three source models refit; fresh gates verified.')


if __name__=='__main__':run()
