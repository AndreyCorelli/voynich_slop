"""Replay the raw/normalized ablation and attribute per-kind/pair changes."""
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_raw_role_evidence_iteration60 import OUT,PREVIOUS,UNIT,MORPH,SOURCE,MODES,ARMS,NORMALIZATIONS,ALL_ARMS,load,save,digest,calibration_frames,evaluate
from voynich_smt.typed_predicate_units import choices,matrix
from voynich_smt.dependency_role_proxy import probabilities,evidence as normalized_evidence,infer,calibrate
from voynich_smt.raw_role_evidence import evidence as raw_evidence


def run():
    hashes=0
    for name in ('design-freeze.json','policy-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];unit_models=load(UNIT/'models.json');proxies=load(PREVIOUS/'models.json');policies=load(OUT/'policies.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};prior=load(PREVIOUS/'frame-predictions.json');by_sid=defaultdict(list)
    for r in prior:by_sid[r['sid']].append(r)
    policy_replays=0;decision_replays=0;normalized_replays=0
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);unit=unit_models[str(f)]['model']
        for mode in MODES:
            frames=calibration_frames(part['calibration'],data,by_sid,unit,proxies[str(f)][mode]['proxy'])
            for n in NORMALIZATIONS:
                for arm in ARMS:
                    assert calibrate(frames[n],arm)==policies[str(f)][n+'_'+mode+'_'+arm];policy_replays+=1
        for sid in part['test']:
            tokens=data[sid]['tokens'];ps={m:probabilities(tokens,proxies[str(f)][m]['proxy']) for m in MODES}
            for old in by_sid.get(sid,[]):
                r=lookup[sid,old['subject']]
                for k,v in old.items():assert r[k]==v
                gold=r['unit_gold'];endpoint=r['arms']['carrierfit_carriercal']['f1']
                for field,oldfield,v in (('ablation_pipeline','role_pipeline',endpoint),('ablation_oracle_endpoint','role_oracle_endpoint',gold[2] if gold else None)):
                    if v is None:
                        for arm in ALL_ARMS:assert r[field][arm] is None;decision_replays+=1
                        continue
                    options=choices(tokens,r['subject'],v);scores=matrix(tokens,r['subject'],v,options)@np.asarray(unit['weights'])
                    for mode,p in ps.items():
                        proxy=proxies[str(f)][mode]['proxy'];pairs={'raw':raw_evidence(v,options,p),'normalized':normalized_evidence(tokens,v,options,p,proxy)}
                        for n,(head,typ) in pairs.items():
                            for arm in ARMS:
                                key=n+'_'+mode+'_'+arm;weight=policies[str(f)][key]['selected'];expected=infer(scores,options,r['subject'],v,head,typ,weight['head_weight'],weight['type_weight']);assert expected==r[field][key];decision_replays+=1
                                if n=='normalized':assert expected==old[oldfield][mode+'_'+arm];normalized_replays+=1
    result=load(OUT/'evaluation.json');assert evaluate(rows)==result;previous=load(PREVIOUS/'evaluation.json');metric_replays=0
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        assert result['unit_metrics'][scope+'/baseline']==previous['unit_metrics'][scope+'/baseline'];metric_replays+=1
        for mode in MODES:
            for arm in ARMS:assert result['unit_metrics'][scope+'/normalized_'+mode+'_'+arm]==previous['unit_metrics'][scope+'/'+mode+'_'+arm];metric_replays+=1
    paired=defaultdict(Counter);kind_changes={}
    for scope in ('selected_sentences','all_source'):
        chosen=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'])]
        for mode in MODES:
            for arm in ARMS:
                raw='raw_'+mode+'_'+arm
                for control in ('baseline','normalized_'+mode+'_'+arm):
                    counts=paired[scope+'/'+raw+'_vs_'+control]
                    for r in chosen:
                        a=r['ablation_pipeline'][control];b=r['ablation_pipeline'][raw];gold=r['unit_gold'];ac=a is not None and a==gold;bc=b is not None and b==gold;aw=a is not None and a!=gold;bw=b is not None and b!=gold
                        counts['correct_added']+=bc and not ac;counts['correct_removed']+=ac and not bc;counts['wrong_added']+=bw and not aw;counts['wrong_removed']+=aw and not bw;counts['predictions_changed']+=a!=b
                kind_changes[scope+'/'+raw]={kind:dict(baseline=result['pipeline_by_gold_kind'][scope+'/baseline/'+kind]['exact'],raw=result['pipeline_by_gold_kind'][scope+'/'+raw+'/'+kind]['exact']) for kind in ('direct','cop','aux')}
    save(OUT/'additional-audit.json',dict(paired={k:dict(v) for k,v in paired.items()},pipeline_kind_changes=kind_changes))
    save(OUT/'independent-validation.json',dict(hash_checks=hashes,calibration_policies_reselected=policy_replays,prediction_fields_replayed=decision_replays,normalized_active_decisions_replayed=normalized_replays,unit_metric_groups_replayed=len(result['unit_metrics']),previous_metric_groups_reproduced=metric_replays,models_refitted=0,prior_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    print({k:dict(v) for k,v in paired.items() if k.endswith(('raw_lexical_joint_vs_baseline','raw_pos_joint_vs_baseline'))});print({k:v for k,v in kind_changes.items() if k.endswith(('raw_lexical_joint','raw_pos_joint'))})
if __name__=='__main__':run()
