"""Refit/replay and ambiguous-head diagnostics for the role proxy experiment."""
from collections import Counter,defaultdict
import math
import numpy as np
from benchmarks.grammar_dependency_role_proxy_iteration59 import OUT,PREVIOUS,UNIT,MORPH,SOURCE,MODES,ARMS,ALL_ARMS,load,save,digest,calibration_frames,evaluate
from voynich_smt.dependency_role_proxy import CLASSES,label,fit,probabilities,pos_prior,evidence,infer,calibrate
from voynich_smt.typed_predicate_units import choices,matrix


def run():
    hashes=0
    for name in ('design-freeze.json','model-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];unit_models=load(UNIT/'models.json');models=load(OUT/'models.json');rows=load(OUT/'frame-predictions.json');prior=load(UNIT/'frame-predictions.json');by_sid=defaultdict(list);old_by_key={(r['sid'],r['subject']):r for r in prior};lookup={(r['sid'],r['subject']):r for r in rows}
    for r in prior:by_sid[r['sid']].append(r)
    refits=0;policy_replays=0;decisions=0;token_confusion={m:np.zeros((4,4),dtype=int) for m in MODES};head_audit=defaultdict(Counter);carrier_audit=defaultdict(Counter);paired=defaultdict(Counter)
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);unit_model=unit_models[str(f)]['model']
        for mode in MODES:
            record=models[str(f)][mode];refit=fit((data[sid]['tokens'] for sid in part['fit']),mode);assert refit['vocabulary']==record['proxy']['vocabulary'];assert np.allclose(refit['weights'],record['proxy']['weights'],rtol=1e-6,atol=1e-7);refits+=1
            cal=calibration_frames(part['calibration'],data,by_sid,unit_model,record['proxy'])
            for arm in ARMS:assert calibrate(cal,arm)==record['policies'][arm];policy_replays+=1
        for sid in part['test']:
            tokens=data[sid]['tokens'];ps={m:probabilities(tokens,models[str(f)][m]['proxy']) for m in MODES}
            for mode,p in ps.items():
                for i,t in enumerate(tokens):token_confusion[mode][CLASSES.index(label(t)),int(np.argmax(p[i]))]+=1
            for old in by_sid.get(sid,[]):
                r=lookup[sid,old['subject']]
                for k,v in old.items():assert r[k]==v
                endpoint=r['arms']['carrierfit_carriercal']['f1'];gold=r['unit_gold']
                for field,v in (('role_pipeline',endpoint),('role_oracle_endpoint',gold[2] if gold else None)):
                    if v is None:
                        for arm in ALL_ARMS:assert r[field][arm] is None;decisions+=1
                        continue
                    options=choices(tokens,r['subject'],v);scores=matrix(tokens,r['subject'],v,options)@np.asarray(unit_model['weights'])
                    for mode,p in ps.items():
                        record=models[str(f)][mode];head,typ=evidence(tokens,v,options,p,record['proxy'])
                        for arm in ARMS:
                            weights=record['policies'][arm]['selected'];prediction=infer(scores,options,r['subject'],v,head,typ,weights['head_weight'],weights['type_weight']);assert prediction==r[field][mode+'_'+arm];decisions+=1
                        if field=='role_oracle_endpoint':
                            truth=CLASSES.index('other' if gold[3]=='direct' else gold[3]);ca=carrier_audit[mode];ca['gold_units']+=1;ca['correct_carrier_role']+=int(np.argmax(p[v]))==truth
                            if gold[3]=='cop':
                                h=gold[1];j=options.index((h,'cop'));count=head_audit[mode];count['gold_copular_heads']+=1;count['gold_head_predicted_dependent']+=int(np.argmax(p[h]))==0;count['gold_head_actually_dependent']+=label(tokens[h])=='dependent'
                                for k,(candidate,role) in enumerate(options):
                                    if role!='cop' or candidate==h or scores[k]<=scores[j]+1e-10:continue
                                    count['higher_scoring_competitors']+=1;count['competitor_predicted_dependent']+=int(np.argmax(p[candidate]))==0;count['competitor_actually_dependent']+=label(tokens[candidate])=='dependent';count['centered_evidence_favors_gold']+=head[j]>head[k]+1e-10;count['centered_evidence_favors_competitor']+=head[k]>head[j]+1e-10;count['raw_non_dependent_favors_gold']+=p[h,0]<p[candidate,0]-1e-10;count['raw_non_dependent_favors_competitor']+=p[candidate,0]<p[h,0]-1e-10
    result=load(OUT/'evaluation.json');assert evaluate(rows)==result;tm=load(OUT/'token-metrics.json')
    for mode in MODES:assert token_confusion[mode].tolist()==tm[mode]['confusion']
    for scope in ('selected_sentences','all_source'):
        selected=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'])]
        for arm in ALL_ARMS:
            for r in selected:
                a=r['role_pipeline']['baseline'];b=r['role_pipeline'][arm];gold=r['unit_gold'];ac=a is not None and a==gold;bc=b is not None and b==gold;aw=a is not None and a!=gold;bw=b is not None and b!=gold;counts=paired[scope+'/'+arm];counts['correct_added']+=bc and not ac;counts['correct_removed']+=ac and not bc;counts['wrong_added']+=bw and not aw;counts['wrong_removed']+=aw and not bw;counts['predictions_changed']+=a!=b
    save(OUT/'additional-audit.json',dict(head_contrasts={k:{a:int(b) for a,b in v.items()} for k,v in head_audit.items()},carrier_role={k:{a:int(b) for a,b in v.items()} for k,v in carrier_audit.items()},paired={k:dict(v) for k,v in paired.items()},warning='Centered/raw probability contrasts are descriptive only; no uncentered score was calibrated or deployed in this experiment.'))
    save(OUT/'independent-validation.json',dict(hash_checks=hashes,proxy_models_refitted=refits,calibration_policies_reselected=policy_replays,prediction_fields_replayed=decisions,unit_metric_groups_replayed=len(result['unit_metrics']),token_confusions_replayed=2,prior_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    print({k:{a:int(b) for a,b in v.items()} for k,v in head_audit.items()});print({k:dict(v) for k,v in paired.items() if k.endswith('lexical_joint')})
if __name__=='__main__':run()
