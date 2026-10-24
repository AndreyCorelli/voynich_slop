"""Refit/replay, head/type oracle contrasts and typed-unit error breakdowns."""
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_typed_predicate_units_iteration57 import OUT,PREVIOUS,MORPH,SOURCE,ARMS,load,save,digest,prepare,evaluate
from voynich_smt.typed_predicate_units import fit,calibrate_distance,gold_unit,choices,matrix,infer,prior_scores,select


def run():
    hashes=0
    for filename in ('design-freeze.json','model-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];models=load(OUT/'models.json');domains=load(OUT/'domain-audit.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};prior={(r['sid'],r['subject']):r for r in load(PREVIOUS/'frame-predictions.json')};refits=0;calibration_replays=0;inference_replays=0;oracle=defaultdict(Counter);confusion=defaultdict(Counter);cop_breakdown=defaultdict(Counter);pipeline_by_role=defaultdict(Counter)
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);training,audit=prepare(part['fit'],data);assert audit==domains[str(f)]['fit'];refit=fit(training);assert np.allclose(refit['weights'],models[str(f)]['model']['weights'],rtol=1e-8,atol=1e-9);refits+=1;del training;cal,audit=prepare(part['calibration'],data);assert audit==domains[str(f)]['calibration'];model=models[str(f)]['model'];assert calibrate_distance(cal,{sid:data[sid]['tokens'] for sid in part['calibration']},model)==models[str(f)]['distance'];calibration_replays+=1;weight=models[str(f)]['distance']['selected']['weight']
        for sid in part['test']:
            tokens=data[sid]['tokens']
            for (row_sid,s),r in lookup.items():
                if row_sid!=sid:continue
                old=prior[sid,s]
                for k,v in old.items():assert r[k]==v
                gold=gold_unit(tokens,s);assert gold==r['unit_gold'];endpoint=r['arms']['carrierfit_carriercal']['f1']
                for arm,w in (('prior_distance',weight),('learned',None)):
                    for name,v in (('unit_pipeline',endpoint),('unit_oracle_endpoint',gold[2] if gold is not None else None)):
                        expected=infer(tokens,s,v,model,w) if v is not None else None;assert expected==r[name][arm];inference_replays+=1
                    if r['carrier_ambiguous'] or gold is None:continue
                    prediction=r['unit_oracle_endpoint'][arm];role=gold[3];scopes=('all_source','selected_sentences') if r['selected_sentence'] else ('all_source',)
                    options=choices(tokens,s,gold[2]);scores=matrix(tokens,s,gold[2],options)@np.asarray(model['weights']) if arm=='learned' else prior_scores(tokens,gold[2],options,model,w)
                    masks={'given_true_type':[j for j,(_,kind) in enumerate(options) if kind==role],'given_true_head':[j for j,(h,_) in enumerate(options) if h==gold[1]]}
                    for scope in scopes:
                        key=scope+'/'+arm+'/'+role;counts=oracle[key];counts['n']+=1;counts['ordinary_exact']+=prediction==gold
                        for mask,indices in masks.items():counts[mask+'_exact']+=select(scores[indices],[options[j] for j in indices],s,gold[2])==gold
                        confusion[scope+'/'+arm][role+'->'+(prediction[3] if prediction is not None else 'tie')]+=1
                        p=pipeline_by_role[key];p['gold']+=1;p['endpoint_correct']+=endpoint==gold[2];p['exact_unit']+=r['unit_pipeline'][arm]==gold
                        if role=='cop':
                            if prediction==gold:reason='exact'
                            elif prediction is None:reason='tie'
                            elif prediction[1]==gold[1]:reason='head_correct_type_wrong'
                            elif prediction[3]==role:reason='type_correct_head_wrong'
                            else:reason='both_wrong'
                            cop_breakdown[scope+'/'+arm][reason]+=1
    replayed=evaluate(rows);evaluation=load(OUT/'evaluation.json');assert replayed==evaluation
    # Group per sentence once: original endpoint metrics must reproduce iteration56.
    previous_evaluation=load(PREVIOUS/'evaluation.json');from benchmarks.grammar_predicate_carriers_iteration56 import evaluate as endpoint_evaluate
    endpoint=endpoint_evaluate(rows)
    for k,v in endpoint.items():assert v==previous_evaluation[k]
    save(OUT/'additional-audit.json',dict(partial_oracles={k:dict(v) for k,v in oracle.items()},role_confusion={k:dict(v) for k,v in confusion.items()},copular_errors={k:dict(v) for k,v in cop_breakdown.items()},pipeline_by_role={k:dict(v) for k,v in pipeline_by_role.items()},warning='True type/head and true endpoints are oracle diagnostics only; no such fields enter actual inference.'))
    save(OUT/'independent-validation.json',dict(hash_checks=hashes,head_models_refitted=refits,distance_policies_reselected=calibration_replays,unit_predictions_replayed=inference_replays,unit_metric_groups_replayed=len(replayed['unit_metrics']),endpoint_metric_groups_replayed=len(endpoint['edges']),previous_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    print({k:dict(v) for k,v in oracle.items() if k.endswith('/cop')});print({k:dict(v) for k,v in pipeline_by_role.items() if k.startswith('selected_sentences/')})
if __name__=='__main__':run()
