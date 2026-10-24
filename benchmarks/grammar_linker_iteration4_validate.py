"""Refit source-only rankers and replay every saved linker experiment."""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import math
import random
import numpy as np

from benchmarks.grammar_linker_iteration4 import (OUT,PREVIOUS,SOURCE_GATE,POOLS,TREEBANKS,
    typed_sentences,grouped,detailed_metrics,summarize)
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.parent_ranking import ConditionalRanker,choices,infer_links
from voynich_smt.predicate_structure import Logistic,morph_features,validate_structure,sentence_features
from voynich_smt.coherent_grammar import finite


def run():
    load=lambda n:json.loads((OUT/n).read_text())
    manifest=load('manifest.json');report=load('report.json');raw_models=load('models.json')
    for p,h in manifest['code_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    source_path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    assert hashlib.sha256(source_path.read_bytes()).hexdigest()==manifest['source_sha256']
    assert hashlib.sha256((PREVIOUS/'model.json').read_bytes()).hexdigest()==manifest['previous_model_sha256']
    assert digest(manifest)==report['manifest_sha256'] and manifest['source_gate']==SOURCE_GATE
    assert not (set(manifest['source_train_ids'])&set(manifest['source_validation_ids']))
    source,_=typed_sentences(source_path,'proiel');by_id={s['sent_id']:s for s in source}
    train=[by_id[sid] for sid in manifest['source_train_ids']]
    validation=[by_id[sid] for sid in manifest['source_validation_ids']]
    assert {s['author'] for s in train+validation}=={'Jerome','Palladius'}
    training=grouped(train);valid=grouped(validation)
    # JSON changes integer dict keys to strings; compare normalized representations.
    assert json.loads(json.dumps(valid))==load('source-validation-truth.json')
    adapter=FrozenAdapter(load('morphology-lattice.json'));models={}
    old=json.loads((PREVIOUS/'model.json').read_text())
    assert raw_models['binary']==old['parent']
    models['binary']=Logistic(**raw_models['binary'])
    for name,typed in [('conditional',False),('typed_conditional',True)]:
        groups=[]
        for s in training:
            morph=[morph_features(adapter.analyze(w)) for w in s['tokens']]
            for c in s['finite']:
                options=choices(s['tokens'],c,s['finite'],morph,typed,radius=None)
                index=next(i for i,r in enumerate(options) if r['parent']==s['parents'][c] and
                    (not typed or r['relation']==s['relations'][c]))
                groups.append(([r['features'] for r in options],index))
        refit=ConditionalRanker.fit_groups(groups);model=ConditionalRanker(**raw_models[name])
        for field in ['weights','mean','scale']:assert np.allclose(getattr(refit,field),getattr(model,field),atol=1e-8,rtol=1e-8)
        assert len(groups)==report['training_counts'][name]['groups']
        models[name]=model
    checked=0
    def verify(row,gold,radius):
        nonlocal checked
        saved=row['prediction'];validate_structure(saved)
        boundaries=gold['boundaries'] if row['boundaries']=='supplied' else None
        logits=Logistic(**old['finite']).probability(sentence_features(gold['tokens'],adapter))
        predicted=[i for i,w in enumerate(gold['tokens']) if any(finite(r) for r in adapter.analyze(w)) and logits[i]>=old['threshold']]
        positions=gold['finite'] if row['evidence']=='oracle_predicates' else predicted
        assert positions==saved['predicates']
        replay=infer_links(gold['tokens'],positions,adapter,models[row['model']],typed=row['model']=='typed_conditional',
            boundaries=boundaries,radius=radius)
        assert replay['status']==saved['status']
        assert replay['forest_score_integer']==saved['forest_score_integer']
        # Check the actual recorded typed witness, not merely its parent graph.
        for child,parent in saved['parents'].items():
            options=saved['arc_candidates'][child];relation=saved['relations'][child]
            if saved['status']=='optimal':assert any(r['parent']==parent and r['relation']==relation for r in options)
            assert math.isclose(sum(r['conditional_probability'] for r in options),1,abs_tol=1e-10)
            actual=replay['arc_candidates'][int(child)]
            assert len(actual)==len(options)
            for a,b in zip(actual,options):
                assert a['parent']==b['parent'] and a['relation']==b['relation']
                assert math.isclose(a['logit'],b['logit'],abs_tol=1e-10)
            if boundaries and parent is not None:
                def region(p):return next(i for i,b in enumerate(boundaries) if p<b)
                assert region(int(child))==region(parent)
        if saved['status']=='optimal':
            witness_score=sum(round(next(o['logit'] for o in saved['arc_candidates'][c] if o['parent']==p and o['relation']==saved['relations'][c])*1000000)
                for c,p in saved['parents'].items())
            assert witness_score==saved['forest_score_integer']
        for metric,baseline in [('metrics',None),('previous_baseline','previous'),('root_baseline','root')]:
            assert detailed_metrics(saved,gold,baseline)==row[metric]
        checked+=1
    source_rows=load('source-validation-predictions.json')
    for row in source_rows:verify(row,valid[row['stream']],None)
    for summary in report['source_summary']:
        chosen=[r for r in source_rows if all(r[k]==summary[k] for k in ['model','evidence','boundaries'])]
        for key in ['metrics','previous_baseline','root_baseline']:assert summarize([r[key] for r in chosen])==summary[key]
    reference=next(r for r in report['source_summary'] if r['model']=='binary' and r['evidence']=='oracle_predicates' and r['boundaries']=='hidden')
    gates={}
    for name in ['conditional','typed_conditional']:
        s=next(r for r in report['source_summary'] if r['model']==name and r['evidence']=='oracle_predicates' and r['boundaries']=='hidden')
        gates[name]=(s['metrics']['edges']['f1']>=s['previous_baseline']['edges']['f1']+SOURCE_GATE['edge_gain'] and
            s['metrics']['roots']['f1']>=reference['metrics']['roots']['f1']-SOURCE_GATE['root_f1_max_loss'] and
            s['metrics']['roots']['recall']>=SOURCE_GATE['root_recall'])
    assert gates==report['source_gate_pass']
    allowed={'binary'}|{name for name,passed in gates.items() if passed}
    assert set(report['target_models_evaluated'])==allowed
    truth={r['id']:r for r in load('target-evaluation-only-truth.json')}
    old_truth={r['id']:r for r in json.loads((PREVIOUS/'evaluation-only-truth.json').read_text())}
    for key,r in truth.items():
        for field in ['tokens','finite','parents','boundaries']:assert r[field]==old_truth[key][field]
    target_rows=load('target-predictions.json')
    assert {r['model'] for r in target_rows}==allowed
    for row in target_rows:verify(row,truth[row['id']],POOLS[row['pool']])
    for summary in report['target_summary']:
        chosen=[r for r in target_rows if all(r[k]==summary[k] for k in ['author','model','evidence','boundaries','pool'])]
        for key in ['metrics','previous_baseline','root_baseline']:assert summarize([r[key] for r in chosen])==summary[key]
    selected=[r for r in source_rows if r['model']=='typed_conditional' and r['evidence']=='oracle_predicates' and r['boundaries']=='hidden']
    rng=random.Random(20261021);draws=[]
    for _ in range(1000):
        sample=rng.choices(selected,k=len(selected))
        def f1(key):
            tp=sum(r[key]['edges']['tp'] for r in sample)
            den=sum(r[key]['edges']['predicted']+r[key]['edges']['gold'] for r in sample)
            return 2*tp/den if den else 0
        draws.append(f1('metrics')-f1('previous_baseline'))
    draws.sort()
    bootstrap={'scope':'Descriptive paired stream-cluster bootstrap of typed minus nearest-previous non-root edge F1; source validation only',
        'seed':20261021,'resamples':1000,'streams':len(selected),'difference_95_interval':[draws[24],draws[974]],'report_sha256':digest(report)}
    if (OUT/'paired-source-bootstrap.json').exists():assert load('paired-source-bootstrap.json')==bootstrap
    else:write_json(OUT/'paired-source-bootstrap.json',bootstrap)
    write_json(OUT/'validation.json',{'validated':True,'forest_replays':checked,'source_models_refitted':2,
        'source_gates':gates,'target_models':sorted(allowed),'report_sha256':digest(report),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'checks':['source-only exact selection and independent refit','disjoint fitting/validation IDs','forest acyclicity, typed witness and optimal score',
                  'ROOT/nonroot metrics and matched baselines','oracle factors explicit','target weights gated on source only','candidate-pool reachability']})
    print('Validated',checked,'forests; both source rankers refit; source gates and target evaluation restrictions verified.')


if __name__=='__main__':run()
